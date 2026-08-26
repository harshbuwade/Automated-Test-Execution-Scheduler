from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ExecutionStatus, TriggerType


class ExecutionCreate(BaseModel):
    test_id: int = Field(..., description="ID of the test script to execute")


class ExecutionSummaryResponse(BaseModel):
    id: int
    test_id: int
    schedule_id: Optional[int] = None
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration: Optional[float] = None
    exit_code: Optional[int] = None
    trigger_type: TriggerType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionDetailResponse(ExecutionSummaryResponse):
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    test_name: Optional[str] = None
    test_framework: Optional[str] = None
    schedule_expression: Optional[str] = None


# Backward compatibility alias
ExecutionResponse = ExecutionDetailResponse


class ExecutionListResponse(BaseModel):
    items: List[ExecutionSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExecutionStatsResponse(BaseModel):
    total_executions: int
    passed: int
    failed: int
    timeout: int
    cancelled: int
    pending: int
    running: int
    success_rate: float = Field(..., description="Percentage of passed runs out of completed executions (passed / (passed+failed+timeout+cancelled) * 100)")
    average_duration: float = Field(..., description="Average duration in seconds of completed test executions")
