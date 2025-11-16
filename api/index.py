from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

try:
    # Try relative imports first (works in production/package context)
    from .models import AvailabilityTime, AvailabilityResponse, AvailabilityRangeResponse, CallerType
    from .fetch_peek_availability import (
        fetch_availability_single_date,
        fetch_availability_date_range,
        parse_availability
    )
    log.info("Using relative imports")
except ImportError:
    # Fall back to absolute imports (works in local development)
    log.warning("Using absolute imports")
    from models import AvailabilityTime, AvailabilityResponse, AvailabilityRangeResponse, CallerType
    from fetch_peek_availability import (
        fetch_availability_single_date,
        fetch_availability_date_range,
        parse_availability
    )

app = FastAPI()

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Cache duration: 5 minutes = 300 seconds
CACHE_MAX_AGE = 300


def add_cache_headers(response: Response) -> Response:
    """Add cache headers to response for 5 minutes."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}"
    return response


def format_skate_times(times: List[AvailabilityTime], date: str) -> str:
    """
    Format availability times into human-readable text.
    
    Args:
        times: List of AvailabilityTime models
        date: Date string in YYYY-MM-DD format
    
    Returns:
        Formatted string with times and spots
    """
    # Parse the date for formatting
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    # Format date: "November 16, 2025" (remove leading zero from day)
    day = date_obj.day
    formatted_date = date_obj.strftime(f"%B {day}, %Y")
    
    lines = [f"For {formatted_date}:"]
    
    for time in times:
        # Format time (already in "7:20PM" format from API)
        lines.append(f"{time.time} has {time.spots} spots")
    
    return "\n".join(lines)


def format_skate_times_range(times: List[AvailabilityTime]) -> str:
    """
    Format availability times across a date range into human-readable text.
    Groups times by date.
    
    Args:
        times: List of AvailabilityTime models
    
    Returns:
        Formatted string with times and spots grouped by date
    """
    from collections import defaultdict
    
    # Group times by date
    times_by_date = defaultdict(list)
    for time in times:
        times_by_date[time.date].append(time)
    
    lines = []
    # Sort dates and format each group
    for date in sorted(times_by_date.keys()):
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %-d, %Y").replace(" 0", " ")  # Remove leading zero from day
        
        lines.append(f"For {formatted_date}:")
        for time in times_by_date[date]:
            lines.append(f"{time.time} has {time.spots} spots")
        lines.append("")  # Empty line between dates
    
    return "\n".join(lines).strip()


@app.get("/")
async def root(response: Response):
    """
    Root endpoint - Serves index.html if available, otherwise returns API info.
    
    **Returns:**
    
    - HTML page with availability checker if static files are available.
    - Otherwise, API information including links to Swagger UI, ReDoc, and OpenAPI JSON documentation.
    """
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    add_cache_headers(response)
    return {
        "message": "Bryant Park Skate Availability API",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }


@app.get("/api")
async def api_info(response: Response):
    """
    API info endpoint - Returns API information and documentation links.
    
    **Returns:**
    
    - API information including links to Swagger UI, ReDoc, and OpenAPI JSON documentation.
    """
    add_cache_headers(response)
    return {
        "message": "Bryant Park Skate Availability API",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }


@app.get("/availability")
async def get_availability(
    response: Response,
    date: Optional[str] = Query(None, description="Date in format YYYY-MM-DD. If not provided, uses current date."),
    caller: Optional[CallerType] = Query(CallerType.API, description="Caller type: USER returns human-readable text, API returns JSON (default)")
):
    """
    Get availability times for a single date.
    
    **Parameters:**
    
    - **date** (`str`, optional): Date in format `YYYY-MM-DD` (e.g., `"2025-11-16"`). If not provided, uses today's date.
    - **caller** (`CallerType`, optional): Caller type enum. `USER` returns human-readable text format, `API` returns JSON format (default: `API`).
    
    **Returns:**
    
    - If `caller=API` (default): `AvailabilityResponse` object with a list of availability times with spots and availability status (filtered to exclude 0 spots).
    - If `caller=USER`: Human-readable plain text format.
    """
    # Use current date if date is not provided
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        raw_data = fetch_availability_single_date(
            date=date
        )
        
        if raw_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch availability data")
        
        parsed = parse_availability(raw_data)
        # Convert to Pydantic models first
        times = [AvailabilityTime(**time) for time in parsed]
        # Filter out times with 0 spots using the model attribute
        filtered_times = [time for time in times if time.spots > 0]
        
        # Return formatted text if caller is USER
        if caller == CallerType.USER:
            formatted_text = format_skate_times(filtered_times, date)
            text_response = PlainTextResponse(content=formatted_text)
            add_cache_headers(text_response)
            return text_response
        
        add_cache_headers(response)
        return AvailabilityResponse(
            date=date,
            count=len(filtered_times),
            times=filtered_times
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/availability/text")
async def get_availability_text(
    response: Response,
    date: Optional[str] = Query(None, description="Date in format YYYY-MM-DD. If not provided, uses current date."),
    caller: Optional[CallerType] = Query(CallerType.USER, description="Caller type: USER returns human-readable text (default), API returns JSON")
):
    """
    Get availability times for a single date in human-readable text format (default).
    
    **Parameters:**
    
    - **date** (`str`, optional): Date in format `YYYY-MM-DD` (e.g., `"2025-11-16"`). If not provided, uses today's date.
    - **caller** (`CallerType`, optional): Caller type enum. `USER` returns human-readable text format (default: `USER`), `API` returns JSON format.
    
    **Returns:**
    
    - If `caller=USER` (default): Human-readable plain text format.
    - If `caller=API`: `AvailabilityResponse` object with a list of availability times with spots and availability status (filtered to exclude 0 spots).
    """
    # Use current date if date is not provided
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        raw_data = fetch_availability_single_date(
            date=date
        )
        
        if raw_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch availability data")
        
        parsed = parse_availability(raw_data)
        # Convert to Pydantic models first
        times = [AvailabilityTime(**time) for time in parsed]
        # Filter out times with 0 spots using the model attribute
        filtered_times = [time for time in times if time.spots > 0]
        
        # Return formatted text if caller is USER (default)
        if caller == CallerType.USER:
            formatted_text = format_skate_times(filtered_times, date)
            text_response = PlainTextResponse(content=formatted_text)
            add_cache_headers(text_response)
            return text_response
        
        add_cache_headers(response)
        return AvailabilityResponse(
            date=date,
            count=len(filtered_times),
            times=filtered_times
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/availability-range")
async def get_availability_range(
    response: Response,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    caller: Optional[CallerType] = Query(CallerType.API, description="Caller type: USER returns human-readable text, API returns JSON (default)")
):
    """
    Get availability for a date range.
    
    **Parameters:**
    
    - **start_date** (`str`, required): Start date in format `YYYY-MM-DD` (e.g., `"2025-11-16"`).
    - **end_date** (`str`, required): End date in format `YYYY-MM-DD` (e.g., `"2025-11-20"`).
    - **caller** (`CallerType`, optional): Caller type enum. `USER` returns human-readable text format, `API` returns JSON format (default: `API`).
    
    **Returns:**
    
    - If `caller=API` (default): `AvailabilityRangeResponse` object with a list of availability times across the date range (filtered to exclude 0 spots).
    - If `caller=USER`: Human-readable plain text format grouped by date.
    """
    try:
        raw_data = fetch_availability_date_range(
            start_date=start_date,
            end_date=end_date
        )
        
        if raw_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch availability data")
        
        parsed = parse_availability(raw_data)
        # Convert to Pydantic models first
        times = [AvailabilityTime(**time) for time in parsed]
        # Filter out times with 0 spots using the model attribute
        filtered_times = [time for time in times if time.spots > 0]
        
        # Return formatted text if caller is USER
        if caller == CallerType.USER:
            formatted_text = format_skate_times_range(filtered_times)
            text_response = PlainTextResponse(content=formatted_text)
            add_cache_headers(text_response)
            return text_response
        
        add_cache_headers(response)
        return AvailabilityRangeResponse(
            start_date=start_date,
            end_date=end_date,
            count=len(filtered_times),
            times=filtered_times
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/availability-range/text")
async def get_availability_range_text(
    response: Response,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    caller: Optional[CallerType] = Query(CallerType.USER, description="Caller type: USER returns human-readable text (default), API returns JSON")
):
    """
    Get availability for a date range in human-readable text format (default).
    
    **Parameters:**
    
    - **start_date** (`str`, required): Start date in format `YYYY-MM-DD` (e.g., `"2025-11-16"`).
    - **end_date** (`str`, required): End date in format `YYYY-MM-DD` (e.g., `"2025-11-20"`).
    - **caller** (`CallerType`, optional): Caller type enum. `USER` returns human-readable text format (default: `USER`), `API` returns JSON format.
    
    **Returns:**
    
    - If `caller=USER` (default): Human-readable plain text format grouped by date.
    - If `caller=API`: `AvailabilityRangeResponse` object with a list of availability times across the date range (filtered to exclude 0 spots).
    """
    try:
        raw_data = fetch_availability_date_range(
            start_date=start_date,
            end_date=end_date
        )
        
        if raw_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch availability data")
        
        parsed = parse_availability(raw_data)
        # Convert to Pydantic models first
        times = [AvailabilityTime(**time) for time in parsed]
        # Filter out times with 0 spots using the model attribute
        filtered_times = [time for time in times if time.spots > 0]
        
        # Return formatted text if caller is USER (default)
        if caller == CallerType.USER:
            formatted_text = format_skate_times_range(filtered_times)
            text_response = PlainTextResponse(content=formatted_text)
            add_cache_headers(text_response)
            return text_response
        
        add_cache_headers(response)
        return AvailabilityRangeResponse(
            start_date=start_date,
            end_date=end_date,
            count=len(filtered_times),
            times=filtered_times
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# This is important for Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)