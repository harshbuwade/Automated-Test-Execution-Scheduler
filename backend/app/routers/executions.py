from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.enums import ExecutionStatus
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionListResponse,
    ExecutionResponse,
)
from app.services.execution_service import (
    get_user_execution_by_id,
    list_user_executions,
    trigger_manual_execution,
)

router = APIRouter(prefix="/executions", tags=["Execution Engine"])


@router.post(
    "",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually trigger test script execution",
    description="Triggers immediate manual execution of a test script owned by the authenticated user.",
)
def create_execution(
    request: ExecutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionResponse:
    """Manual execution endpoint."""
    execution = trigger_manual_execution(
        db=db,
        user_id=current_user.id,
        test_id=request.test_id,
    )
    return execution


@router.get(
    "",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's test execution records",
    description="Returns a paginated list of execution logs for tests belonging to the authenticated user.",
)
def list_executions(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    test_id: Optional[int] = Query(None, description="Filter executions by test ID"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter executions by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionListResponse:
    """List execution records endpoint with pagination and optional filtering."""
    items, total, total_pages = list_user_executions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        test_id=test_id,
        status_filter=status,
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
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single test execution record",
    description="Retrieves execution details by ID if the test belongs to the authenticated user.",
)
def get_execution_by_id(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionResponse:
    """Get single execution endpoint."""
    return get_user_execution_by_id(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
    )
