from datetime import datetime
import math
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from app.execution.runner import run_pytest_script
from app.models.enums import ExecutionStatus, TriggerType
from app.models.execution import Execution
from app.models.schedule import Schedule
from app.models.test import Test
from app.schemas.execution import (
    ExecutionDetailResponse,
    ExecutionStatsResponse,
    ExecutionSummaryResponse,
)
from app.services.test_service import get_user_test_by_id


def validate_date_range(date_from: Optional[datetime], date_to: Optional[datetime]):
    """Validates that date_from <= date_to if both are provided."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be less than or equal to date_to.",
        )


def trigger_manual_execution(db: Session, user_id: int, test_id: int) -> ExecutionDetailResponse:
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

    return get_user_execution_by_id(db, user_id, execution.id)


def list_user_executions(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    test_id: Optional[int] = None,
    schedule_id: Optional[int] = None,
    status_filter: Optional[ExecutionStatus] = None,
    trigger_type_filter: Optional[TriggerType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Tuple[List[Execution], int, int]:
    """Retrieves paginated execution logs belonging to user's tests."""
    validate_date_range(date_from, date_to)

    query = db.query(Execution).join(Test, Execution.test_id == Test.id).filter(Test.user_id == user_id)

    if test_id is not None:
        query = query.filter(Execution.test_id == test_id)

    if schedule_id is not None:
        query = query.filter(Execution.schedule_id == schedule_id)

    if status_filter is not None:
        query = query.filter(Execution.status == status_filter)

    if trigger_type_filter is not None:
        query = query.filter(Execution.trigger_type == trigger_type_filter)

    if date_from is not None:
        query = query.filter(Execution.created_at >= date_from)

    if date_to is not None:
        query = query.filter(Execution.created_at <= date_to)

    total_count = query.with_entities(func.count(Execution.id)).scalar() or 0
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    offset = (page - 1) * page_size

    items = query.order_by(Execution.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total_count, total_pages


def get_recent_user_executions(
    db: Session,
    user_id: int,
    limit: int = 10,
) -> List[Execution]:
    """Retrieves the N most recent execution records belonging to user's tests."""
    safe_limit = min(max(limit, 1), 50)
    return (
        db.query(Execution)
        .join(Test, Execution.test_id == Test.id)
        .filter(Test.user_id == user_id)
        .order_by(Execution.created_at.desc())
        .limit(safe_limit)
        .all()
    )


def get_test_executions(
    db: Session,
    user_id: int,
    test_id: int,
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[ExecutionStatus] = None,
    trigger_type_filter: Optional[TriggerType] = None,
) -> Tuple[List[Execution], int, int]:
    """Retrieves execution history for a specific test ensuring ownership."""
    # Verify test ownership (raises 404 if not found/owned)
    get_user_test_by_id(db, user_id, test_id)

    return list_user_executions(
        db=db,
        user_id=user_id,
        page=page,
        page_size=page_size,
        test_id=test_id,
        status_filter=status_filter,
        trigger_type_filter=trigger_type_filter,
    )


def get_schedule_executions(
    db: Session,
    user_id: int,
    schedule_id: int,
    page: int = 1,
    page_size: int = 10,
) -> Tuple[List[Execution], int, int]:
    """Retrieves execution history generated by a specific schedule ensuring ownership."""
    # Verify schedule ownership via Schedule -> Test -> User
    schedule = (
        db.query(Schedule)
        .join(Test, Schedule.test_id == Test.id)
        .filter(Schedule.id == schedule_id, Test.user_id == user_id)
        .first()
    )
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found.",
        )

    return list_user_executions(
        db=db,
        user_id=user_id,
        page=page,
        page_size=page_size,
        schedule_id=schedule_id,
    )


def get_user_execution_by_id(db: Session, user_id: int, execution_id: int) -> ExecutionDetailResponse:
    """Retrieves a single detailed execution record ensuring the underlying test belongs to user_id."""
    record = (
        db.query(Execution, Test.name, Test.framework, Schedule.schedule_expression)
        .join(Test, Execution.test_id == Test.id)
        .outerjoin(Schedule, Execution.schedule_id == Schedule.id)
        .filter(Execution.id == execution_id, Test.user_id == user_id)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )

    execution, test_name, test_framework, schedule_expr = record

    return ExecutionDetailResponse(
        id=execution.id,
        test_id=execution.test_id,
        schedule_id=execution.schedule_id,
        status=execution.status,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        duration=execution.duration,
        exit_code=execution.exit_code,
        stdout=execution.stdout,
        stderr=execution.stderr,
        trigger_type=execution.trigger_type,
        created_at=execution.created_at,
        test_name=test_name,
        test_framework=test_framework,
        schedule_expression=schedule_expr,
    )


def get_user_execution_stats(
    db: Session,
    user_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> ExecutionStatsResponse:
    """Calculates aggregate execution statistics for the authenticated user via SQL aggregation."""
    validate_date_range(date_from, date_to)

    query = db.query(Execution).join(Test, Execution.test_id == Test.id).filter(Test.user_id == user_id)

    if date_from is not None:
        query = query.filter(Execution.created_at >= date_from)

    if date_to is not None:
        query = query.filter(Execution.created_at <= date_to)

    stats = query.with_entities(
        func.count(Execution.id).label("total"),
        func.sum(case((Execution.status == ExecutionStatus.PASSED, 1), else_=0)).label("passed"),
        func.sum(case((Execution.status == ExecutionStatus.FAILED, 1), else_=0)).label("failed"),
        func.sum(case((Execution.status == ExecutionStatus.TIMEOUT, 1), else_=0)).label("timeout"),
        func.sum(case((Execution.status == ExecutionStatus.CANCELLED, 1), else_=0)).label("cancelled"),
        func.sum(case((Execution.status == ExecutionStatus.PENDING, 1), else_=0)).label("pending"),
        func.sum(case((Execution.status == ExecutionStatus.RUNNING, 1), else_=0)).label("running"),
        func.avg(
            case(
                (
                    Execution.status.in_(
                        [
                            ExecutionStatus.PASSED,
                            ExecutionStatus.FAILED,
                            ExecutionStatus.TIMEOUT,
                            ExecutionStatus.CANCELLED,
                        ]
                    ),
                    Execution.duration,
                ),
                else_=None,
            )
        ).label("avg_dur"),
    ).first()

    total_executions = stats.total or 0
    passed = stats.passed or 0
    failed = stats.failed or 0
    timeout = stats.timeout or 0
    cancelled = stats.cancelled or 0
    pending = stats.pending or 0
    running = stats.running or 0

    completed_executions = passed + failed + timeout + cancelled
    success_rate = round((passed / completed_executions) * 100.0, 2) if completed_executions > 0 else 0.0
    average_duration = round(float(stats.avg_dur), 2) if stats.avg_dur is not None else 0.0

    return ExecutionStatsResponse(
        total_executions=total_executions,
        passed=passed,
        failed=failed,
        timeout=timeout,
        cancelled=cancelled,
        pending=pending,
        running=running,
        success_rate=success_rate,
        average_duration=average_duration,
    )


def trigger_scheduled_execution(test_id: int, schedule_id: int):
    """Executes a test script triggered automatically by APScheduler."""
    import logging
    from app.database import SessionLocal
    from app.scheduler.manager import calculate_next_run

    logger = logging.getLogger("test_scheduler.scheduled_exec")
    db = SessionLocal()

    try:
        test = db.query(Test).filter(Test.id == test_id).first()
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

        if not test or not schedule or not schedule.is_active:
            logger.warning(f"Scheduled execution skipped: test_id={test_id}, schedule_id={schedule_id} inactive or missing.")
            return

        # 1. Create PENDING execution record
        execution = Execution(
            test_id=test.id,
            schedule_id=schedule.id,
            status=ExecutionStatus.PENDING,
            trigger_type=TriggerType.SCHEDULED,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        # 2. Transition status to RUNNING
        execution.status = ExecutionStatus.RUNNING
        db.commit()

        # 3. Execute runner
        result = run_pytest_script(test.script_path, test.timeout)

        # 4. Persist execution results
        execution.status = result["status"]
        execution.started_at = result["started_at"]
        execution.finished_at = result["finished_at"]
        execution.duration = result["duration"]
        execution.exit_code = result["exit_code"]
        execution.stdout = result["stdout"]
        execution.stderr = result["stderr"]

        # 5. Update Schedule last_run and next_run
        schedule.last_run = result["finished_at"]
        schedule.next_run = calculate_next_run(schedule.schedule_type, schedule.schedule_expression)

        db.commit()
        logger.info(f"Scheduled execution completed: schedule_id={schedule_id}, status={execution.status}")

    except Exception as exc:
        logger.error(f"Error executing scheduled job test_id={test_id}, schedule_id={schedule_id}: {exc}", exc_info=True)
        db.rollback()
    finally:
        db.close()
