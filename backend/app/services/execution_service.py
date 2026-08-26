import math
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.execution.runner import run_pytest_script
from app.models.enums import ExecutionStatus, TriggerType
from app.models.execution import Execution
from app.models.test import Test
from app.services.test_service import get_user_test_by_id


def trigger_manual_execution(db: Session, user_id: int, test_id: int) -> Execution:
    """Triggers manual execution of a test script owned by user_id."""
    # 1. Validate test existence & ownership (raises 404 if not owned/found)
    test = get_user_test_by_id(db, user_id, test_id)

    # 2. Create initial PENDING execution record
    execution = Execution(
        test_id=test.id,
        schedule_id=None,
        status=ExecutionStatus.PENDING,
        trigger_type=TriggerType.MANUAL,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # 3. Transition status to RUNNING
    execution.status = ExecutionStatus.RUNNING
    db.commit()

    # 4. Execute test script in isolated subprocess runner
    result = run_pytest_script(test.script_path, test.timeout)

    # 5. Persist execution results
    execution.status = result["status"]
    execution.started_at = result["started_at"]
    execution.finished_at = result["finished_at"]
    execution.duration = result["duration"]
    execution.exit_code = result["exit_code"]
    execution.stdout = result["stdout"]
    execution.stderr = result["stderr"]

    db.commit()
    db.refresh(execution)
    return execution


def list_user_executions(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    test_id: Optional[int] = None,
    status_filter: Optional[ExecutionStatus] = None,
) -> Tuple[List[Execution], int, int]:
    """Retrieves paginated execution logs belonging to user's tests."""
    query = db.query(Execution).join(Test, Execution.test_id == Test.id).filter(Test.user_id == user_id)

    if test_id is not None:
        query = query.filter(Execution.test_id == test_id)

    if status_filter is not None:
        query = query.filter(Execution.status == status_filter)

    total_count = query.with_entities(func.count(Execution.id)).scalar() or 0
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    offset = (page - 1) * page_size

    items = query.order_by(Execution.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total_count, total_pages


def get_user_execution_by_id(db: Session, user_id: int, execution_id: int) -> Execution:
    """Retrieves a single execution record ensuring the underlying test belongs to user_id."""
    execution = (
        db.query(Execution)
        .join(Test, Execution.test_id == Test.id)
        .filter(Execution.id == execution_id, Test.user_id == user_id)
        .first()
    )

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )
    return execution
