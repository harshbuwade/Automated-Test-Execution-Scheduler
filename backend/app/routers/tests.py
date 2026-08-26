from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from typing import Optional
from app.models.enums import ExecutionStatus, TriggerType
from app.schemas.execution import ExecutionListResponse
from app.schemas.test import (
    TestCreate,
    TestListResponse,
    TestResponse,
    TestUpdate,
)

from app.services.test_service import (
    create_test,
    delete_user_test,
    get_user_test_by_id,
    list_user_tests,
    update_user_test,
)

router = APIRouter(prefix="/tests", tags=["Test Management"])


@router.post(
    "",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test script definition",
    description="Creates a new automated test definition associated with the currently authenticated user.",
)
def create_new_test(
    request: TestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestResponse:
    """Create test endpoint."""
    return create_test(db=db, user_id=current_user.id, test_in=request)


@router.get(
    "",
    response_model=TestListResponse,
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's test script definitions",
    description="Returns a paginated list of test script definitions owned by the authenticated user.",
)
def list_tests(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestListResponse:
    """List user tests endpoint with pagination."""
    items, total, total_pages = list_user_tests(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return TestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{test_id}",
    response_model=TestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single test script definition",
    description="Retrieves a test script definition by ID if it belongs to the authenticated user. Returns 404 otherwise.",
)
def get_test_by_id(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestResponse:
    """Get single test endpoint."""
    return get_user_test_by_id(db=db, user_id=current_user.id, test_id=test_id)


@router.put(
    "/{test_id}",
    response_model=TestResponse,
    status_code=status.HTTP_200_OK,
    summary="Update test script definition",
    description="Updates a test script definition by ID if it belongs to the authenticated user.",
)
def update_test(
    test_id: int,
    request: TestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestResponse:
    """Update test endpoint."""
    return update_user_test(db=db, user_id=current_user.id, test_id=test_id, test_in=request)


@router.delete(
    "/{test_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete test script definition",
    description="Deletes a test script definition by ID if it belongs to the authenticated user.",
)
def delete_test(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete test endpoint."""
    delete_user_test(db=db, user_id=current_user.id, test_id=test_id)
    return {"detail": "Test deleted successfully."}


@router.get(
    "/{test_id}/executions",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get execution history for a specific test",
    description="Returns a paginated execution history for a specific test script owned by the user.",
)
def get_test_executions_history(
    test_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter executions by status"),
    trigger_type: Optional[TriggerType] = Query(None, description="Filter executions by trigger type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutionListResponse:
    """Test-specific execution history endpoint."""
    from typing import Optional
    from app.models.enums import ExecutionStatus, TriggerType
    from app.schemas.execution import ExecutionListResponse
    from app.services.execution_service import get_test_executions

    items, total, total_pages = get_test_executions(
        db=db,
        user_id=current_user.id,
        test_id=test_id,
        page=page,
        page_size=page_size,
        status_filter=status,
        trigger_type_filter=trigger_type,
    )
    return ExecutionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

