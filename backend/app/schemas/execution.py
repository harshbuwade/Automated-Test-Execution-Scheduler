from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ExecutionStatus, TriggerType


class ExecutionCreate(BaseModel):
    test_id: int = Field(..., description="ID of the test script to execute")


class ExecutionResponse(BaseModel):
    id: int
    test_id: int
    schedule_id: Optional[int] = None
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration: Optional[float] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    trigger_type: TriggerType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionListResponse(BaseModel):
    items: List[ExecutionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
