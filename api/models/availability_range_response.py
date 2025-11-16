from pydantic import BaseModel
from typing import List
from .availability_time import AvailabilityTime


class AvailabilityRangeResponse(BaseModel):
    start_date: str
    end_date: str
    count: int
    times: List[AvailabilityTime]

