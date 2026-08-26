from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.enums import ExecutionStatus, TriggerType
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionDetailResponse,
    ExecutionListResponse,
    ExecutionStatsResponse,
    ExecutionSummaryResponse,
)
from app.services.execution_service import (
    get_recent_user_executions,
    get_user_execution_by_id,
    get_user_execution_stats,
    list_user_executions,
    trigger_manual_execution,
)

router = APIRouter(prefix="/executions", tags=["Execution Engine & Reporting"])


@router.post(
    "",
    response_model=ExecutionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually trigger test script execution",
    description="Triggers immediate manual execution of a test script owned by the authenticated user.",
)
def create_execution(
    request: ExecutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionDetailResponse:
    """Manual execution endpoint."""
    return trigger_manual_execution(
        db=db,
        user_id=current_user.id,
        test_id=request.test_id,
    )


@router.get(
    "/recent",
    response_model=List[ExecutionSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recent execution records",
    description="Returns the N most recent execution logs (default 10, max 50) for the authenticated user.",
)
def get_recent_executions(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recent records to return (1-50)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ExecutionSummaryResponse]:
    """Recent executions endpoint."""
    return get_recent_user_executions(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )


@router.get(
    "/stats",
    response_model=ExecutionStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get execution statistics & reporting metrics",
    description="Returns aggregate execution statistics (counts, success_rate, average_duration) for tests owned by the user.",
)
def get_execution_stats(
    date_from: Optional[datetime] = Query(None, description="Start date filter (UTC)"),
    date_to: Optional[datetime] = Query(None, description="End date filter (UTC)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionStatsResponse:
    """Execution reporting statistics endpoint."""
    return get_user_execution_stats(
        db=db,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's test execution records",
    description="Returns a paginated list of summary execution logs for tests belonging to the authenticated user.",
)
def list_executions(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    test_id: Optional[int] = Query(None, description="Filter executions by test ID"),
    schedule_id: Optional[int] = Query(None, description="Filter executions by schedule ID"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter executions by status"),
    trigger_type: Optional[TriggerType] = Query(None, description="Filter executions by trigger type (manual or scheduled)"),
    date_from: Optional[datetime] = Query(None, description="Start date filter (UTC)"),
    date_to: Optional[datetime] = Query(None, description="End date filter (UTC)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionListResponse:
    """List execution records endpoint with pagination and filtering."""
    items, total, total_pages = list_user_executions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        test_id=test_id,
        schedule_id=schedule_id,
        status_filter=status,
        trigger_type_filter=trigger_type,
        date_from=date_from,
        date_to=date_to,
    )
    return ExecutionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{execution_id}",
    response_model=ExecutionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single test execution record detail",
    description="Retrieves execution details (including stdout/stderr logs and test metadata) by ID if owned by user.",
)
def get_execution_by_id(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionDetailResponse:
    """Get single execution detail endpoint."""
    return get_user_execution_by_id(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
    )
