from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.enums import ScheduleType
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.execution import ExecutionListResponse
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
)

from app.services.schedule_service import (
    create_schedule,
    delete_user_schedule,
    get_user_schedule_by_id,
    list_user_schedules,
    pause_user_schedule,
    resume_user_schedule,
    update_user_schedule,
)

router = APIRouter(prefix="/schedules", tags=["Scheduling Engine"])


@router.post(
    "",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create test schedule",
    description="Creates a new execution schedule (interval or cron) associated with a test script owned by the user.",
)
def create_new_schedule(
    request: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    """Create schedule endpoint."""
    schedule = create_schedule(
        db=db,
        user_id=current_user.id,
        schedule_in=request,
    )
    return schedule


@router.get(
    "",
    response_model=ScheduleListResponse,
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's schedules",
    description="Returns a paginated list of execution schedules for tests belonging to the user.",
)
def list_schedules(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    test_id: Optional[int] = Query(None, description="Filter schedules by test ID"),
    is_active: Optional[bool] = Query(None, description="Filter schedules by active state"),
    schedule_type: Optional[ScheduleType] = Query(None, description="Filter schedules by type (interval or cron)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleListResponse:
    """List schedules endpoint."""
    items, total, total_pages = list_user_schedules(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        test_id=test_id,
        is_active=is_active,
        schedule_type=schedule_type,
    )
    return ScheduleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single schedule by ID",
    description="Retrieves single schedule details if associated test belongs to the authenticated user.",
)
def get_schedule_by_id(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    """Get schedule endpoint."""
    return get_user_schedule_by_id(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
    )


@router.put(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update schedule by ID",
    description="Updates schedule type, expression, or active state and reconfigures APScheduler job.",
)
def update_schedule(
    schedule_id: int,
    request: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    """Update schedule endpoint."""
    return update_user_schedule(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
        schedule_in=request,
    )


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete schedule by ID",
    description="Deletes schedule, removes APScheduler job, and preserves execution logs.",
)
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete schedule endpoint."""
    delete_user_schedule(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
    )
    return {"detail": "Schedule deleted successfully."}


@router.post(
    "/{schedule_id}/pause",
    response_model=ScheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Pause schedule by ID",
    description="Sets is_active=false and removes APScheduler job.",
)
def pause_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    """Pause schedule endpoint."""
    return pause_user_schedule(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
    )


@router.post(
    "/{schedule_id}/resume",
    response_model=ScheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume schedule by ID",
    description="Sets is_active=true and registers APScheduler job.",
)
def resume_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    """Resume schedule endpoint."""
    return resume_user_schedule(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
    )


@router.get(
    "/{schedule_id}/executions",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get execution history for a specific schedule",
    description="Returns a paginated execution history generated by a specific schedule owned by the user.",
)
def get_schedule_executions_history(
    schedule_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionListResponse:
    """Schedule-specific execution history endpoint."""
    from app.schemas.execution import ExecutionListResponse
    from app.services.execution_service import get_schedule_executions

    items, total, total_pages = get_schedule_executions(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
        page=page,
        page_size=page_size,
    )
    return ExecutionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

