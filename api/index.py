from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from .fetch_peek_availability import (
    fetch_availability_single_date,
    fetch_availability_date_range,
    parse_availability
)

app = FastAPI()


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "message": "Peek Availability API",
        "endpoints": {
            "/availability/{date}": "Get availability for a single date",
            "/availability-range": "Get availability for a date range"
        }
    }


@app.get("/availability/{date}")
async def get_availability(
    date: str,
    booking_refid: Optional[str] = Query(None, description="Optional booking reference ID")
):
    """
    Get availability times for a single date.
    
    Args:
        date: Date in format YYYY-MM-DD (e.g., "2025-11-16")
        booking_refid: Optional booking reference ID
    
    Returns:
        List of availability times with spots and availability status
    """
    try:
        raw_data = fetch_availability_single_date(
            date=date,
            booking_refid=booking_refid
        )
        
        if raw_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch availability data")
        
        parsed = parse_availability(raw_data)
        return {
            "date": date,
            "count": len(parsed),
            "times": parsed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/availability-range")
async def get_availability_range(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    booking_refid: Optional[str] = Query(None, description="Optional booking reference ID"),
    namespace: Optional[str] = Query(None, description="Optional namespace parameter"),
    pc_id: Optional[str] = Query(None, description="Optional product configuration ID")
):
    """
    Get availability for a date range.
    
    Args:
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD
        booking_refid: Optional booking reference ID
        namespace: Optional namespace parameter
        pc_id: Optional product configuration ID
    
    Returns:
        List of availability times across the date range
    """
    try:
        raw_data = fetch_availability_date_range(
            start_date=start_date,
            end_date=end_date,
            booking_refid=booking_refid,
            namespace=namespace,
            pc_id=pc_id
        )
        
        if raw_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch availability data")
        
        parsed = parse_availability(raw_data)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "count": len(parsed),
            "times": parsed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
