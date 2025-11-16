from pydantic import BaseModel
from typing import List
from .availability_time import AvailabilityTime


class AvailabilityResponse(BaseModel):
    date: str
    count: int
    times: List[AvailabilityTime]

