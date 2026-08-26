from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ScheduleType


class ScheduleCreate(BaseModel):
    test_id: int = Field(..., description="ID of test script to schedule")
    schedule_type: ScheduleType = Field(..., description="Schedule type: interval or cron")
    schedule_expression: str = Field(
        ...,
        description="Schedule expression: integer seconds for interval (e.g. '60') or 5-field cron string (e.g. '0 9 * * *')",
    )
    is_active: bool = Field(True, description="Whether the schedule is immediately active")


class ScheduleUpdate(BaseModel):
    schedule_type: Optional[ScheduleType] = Field(None, description="Updated schedule type: interval or cron")
    schedule_expression: Optional[str] = Field(None, description="Updated schedule expression")
    is_active: Optional[bool] = Field(None, description="Updated active status")


class ScheduleResponse(BaseModel):
    id: int
    test_id: int
    schedule_type: ScheduleType
    schedule_expression: str
    is_active: bool
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleListResponse(BaseModel):
    items: List[ScheduleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
