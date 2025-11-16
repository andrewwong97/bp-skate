from enum import Enum


class CallerType(str, Enum):
    """Caller type enum for response format selection"""
    USER = "USER"  # Returns human-readable text format
    API = "API"    # Returns JSON format (default)

