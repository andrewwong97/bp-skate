from pydantic import BaseModel
from typing import Optional


class AvailabilityTime(BaseModel):
    time: str
    date: str
    spots: int
    availability_mode: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None

