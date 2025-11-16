import os
import time
from typing import Optional
from functools import wraps

from upstash_redis import Redis

# Redis connection configuration
# For Vercel/serverless: Use Upstash Redis REST API
# Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN
# If not set, rate limiting will be disabled (noop)
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", None)
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", None)

# Rate limiting configuration
# Default: 30 requests per hour
DEFAULT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))
DEFAULT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600"))  # 1 hour


class RateLimiter:
    """
    Redis-based rate limiter for Peek API calls using Upstash Redis.
    
    Uses a sliding window approach to limit the number of API calls
    within a specified time window.
    
    If Upstash Redis is not configured, this becomes a noop (allows all requests).
    """
    
    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ):
        """
        Initialize the rate limiter.
        
        Args:
            redis_client: Optional Redis client instance. If not provided, creates a new one.
            max_requests: Maximum number of requests allowed in the time window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        if redis_client:
            self.redis_client = redis_client
        elif UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
            try:
                self.redis_client = Redis(
                    url=UPSTASH_REDIS_REST_URL,
                    token=UPSTASH_REDIS_REST_TOKEN,
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Could not connect to Upstash Redis: {e}")
                print("Rate limiting will be disabled (noop).")
                self.redis_client = None
        else:
            # No Redis configuration - rate limiting disabled (noop)
            self.redis_client = None
    
    def _get_key(self, identifier: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"rate_limit:peek_api:{identifier}"
    
    def is_allowed(self, identifier: str = "default") -> tuple[bool, Optional[dict]]:
        """
        Check if a request is allowed based on rate limiting.
        
        If Redis is not configured, always returns True (noop).
        
        Args:
            identifier: Unique identifier for the rate limit (e.g., IP address, user ID, or "default" for global)
        
        Returns:
            tuple: (is_allowed: bool, info: dict with remaining requests and reset time)
        """
        # If Redis is not configured, allow all requests (noop)
        if not self.redis_client:
            return True, {
                "allowed": True,
                "remaining": None,
                "limit": self.max_requests,
                "window_seconds": self.window_seconds,
                "note": "Rate limiting disabled (no Redis configuration)",
            }
        
        key = self._get_key(identifier)
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        try:
            # Use Redis sorted set for sliding window
            # Remove old entries outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in the window
            current_count = self.redis_client.zcard(key)
            
            if current_count >= self.max_requests:
                # Rate limit exceeded
                # Get the oldest entry to calculate when the limit will reset
                oldest_entry = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_entry:
                    reset_time = oldest_entry[0][1] + self.window_seconds
                    reset_in = int(reset_time - current_time)
                else:
                    reset_in = self.window_seconds
                
                return False, {
                    "allowed": False,
                    "remaining": 0,
                    "reset_in_seconds": max(0, reset_in),
                    "limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                }
            
            # Add current request to the sorted set
            self.redis_client.zadd(key, {str(current_time): current_time})
            # Set expiration on the key (window_seconds + buffer)
            self.redis_client.expire(key, self.window_seconds + 60)
            
            remaining = self.max_requests - current_count - 1
            
            return True, {
                "allowed": True,
                "remaining": max(0, remaining),
                "reset_in_seconds": self.window_seconds,
                "limit": self.max_requests,
                "window_seconds": self.window_seconds,
            }
            
        except Exception as e:
            print(f"Redis error in rate limiter: {e}")
            # On Redis error, allow the request but log the error
            return True, {
                "allowed": True,
                "remaining": None,
                "error": str(e),
            }
    
    def reset(self, identifier: str = "default") -> bool:
        """
        Reset the rate limit for a given identifier.
        
        Args:
            identifier: Unique identifier for the rate limit
        
        Returns:
            bool: True if reset was successful, False if Redis is not configured
        """
        if not self.redis_client:
            return False
        
        key = self._get_key(identifier)
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis error resetting rate limit: {e}")
            return False


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(
    max_requests: int = DEFAULT_MAX_REQUESTS,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> RateLimiter:
    """
    Get or create the global rate limiter instance.
    
    Args:
        max_requests: Maximum number of requests allowed in the time window.
        window_seconds: Time window in seconds.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
    return _rate_limiter


def check_rate_limit(identifier: str = "default") -> tuple[bool, Optional[dict]]:
    """
    Convenience function to check rate limit.
    
    Args:
        identifier: Unique identifier for the rate limit
    
    Returns:
        tuple: (is_allowed: bool, info: dict)
    """
    limiter = get_rate_limiter()
    return limiter.is_allowed(identifier)


def rate_limit_decorator(identifier_func=None):
    """
    Decorator to rate limit function calls.
    
    Usage:
        @rate_limit_decorator(lambda: request.client.host)
        def my_function():
            ...
    
    Args:
        identifier_func: Function that returns the identifier for rate limiting.
                         If None, uses "default" for all calls.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if identifier_func:
                identifier = identifier_func()
            else:
                identifier = "default"
            
            allowed, info = check_rate_limit(identifier)
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please try again in {info.get('reset_in_seconds', 0)} seconds.",
                        "remaining": info.get("remaining", 0),
                        "reset_in_seconds": info.get("reset_in_seconds", 0),
                    }
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
