import math
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.enums import ScheduleType
from app.models.schedule import Schedule
from app.models.test import Test
from app.scheduler.manager import (
    build_apscheduler_trigger,
    calculate_next_run,
    scheduler_manager,
)
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.execution_service import trigger_scheduled_execution
from app.services.test_service import get_user_test_by_id


def validate_schedule_expression(schedule_type: ScheduleType, schedule_expression: str):
    """Validates schedule expression format.

    Raises HTTPException(400) if invalid.
    """
    try:
        build_apscheduler_trigger(schedule_type, schedule_expression)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def create_schedule(db: Session, user_id: int, schedule_in: ScheduleCreate) -> Schedule:
    """Creates a schedule for a test owned by user_id and registers APScheduler job."""
    # 1. Verify test ownership (raises 404 if not found / not owned)
    test = get_user_test_by_id(db, user_id, schedule_in.test_id)

    # 2. Validate schedule expression
    validate_schedule_expression(schedule_in.schedule_type, schedule_in.schedule_expression)

    # 3. Calculate next_run
    next_run = calculate_next_run(schedule_in.schedule_type, schedule_in.schedule_expression) if schedule_in.is_active else None

    # 4. Create Schedule record
    schedule = Schedule(
        test_id=test.id,
        schedule_type=schedule_in.schedule_type,
        schedule_expression=schedule_in.schedule_expression.strip(),
        is_active=schedule_in.is_active,
        next_run=next_run,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # 5. Register job in APScheduler
    scheduler_manager.add_or_update_schedule_job(schedule, trigger_scheduled_execution)

    return schedule


def list_user_schedules(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    test_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    schedule_type: Optional[ScheduleType] = None,
) -> Tuple[List[Schedule], int, int]:
    """Retrieves paginated schedules belonging to user's tests."""
    query = db.query(Schedule).join(Test, Schedule.test_id == Test.id).filter(Test.user_id == user_id)

    if test_id is not None:
        query = query.filter(Schedule.test_id == test_id)

    if is_active is not None:
        query = query.filter(Schedule.is_active == is_active)

    if schedule_type is not None:
        query = query.filter(Schedule.schedule_type == schedule_type)

    total_count = query.with_entities(func.count(Schedule.id)).scalar() or 0
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    offset = (page - 1) * page_size

    items = query.order_by(Schedule.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total_count, total_pages


def get_user_schedule_by_id(db: Session, user_id: int, schedule_id: int) -> Schedule:
    """Retrieves a single schedule record ensuring the associated test belongs to user_id."""
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
    return schedule


def update_user_schedule(
    db: Session,
    user_id: int,
    schedule_id: int,
    schedule_in: ScheduleUpdate,
) -> Schedule:
    """Updates an existing schedule record and reconfigures APScheduler job."""
    schedule = get_user_schedule_by_id(db, user_id, schedule_id)

    new_type = schedule_in.schedule_type if schedule_in.schedule_type is not None else schedule.schedule_type
    new_expr = schedule_in.schedule_expression if schedule_in.schedule_expression is not None else schedule.schedule_expression
    new_active = schedule_in.is_active if schedule_in.is_active is not None else schedule.is_active

    validate_schedule_expression(new_type, new_expr)

    schedule.schedule_type = new_type
    schedule.schedule_expression = new_expr.strip()
    schedule.is_active = new_active
    schedule.next_run = calculate_next_run(new_type, new_expr) if new_active else None

    db.commit()
    db.refresh(schedule)

    scheduler_manager.add_or_update_schedule_job(schedule, trigger_scheduled_execution)

    return schedule


def delete_user_schedule(db: Session, user_id: int, schedule_id: int):
    """Deletes a schedule, removes its APScheduler job, and preserves past execution records."""
    schedule = get_user_schedule_by_id(db, user_id, schedule_id)

    scheduler_manager.remove_schedule_job(schedule.id)

    db.delete(schedule)
    db.commit()


def pause_user_schedule(db: Session, user_id: int, schedule_id: int) -> Schedule:
    """Pauses an active schedule and removes its APScheduler job."""
    schedule = get_user_schedule_by_id(db, user_id, schedule_id)

    schedule.is_active = False
    schedule.next_run = None
    db.commit()
    db.refresh(schedule)

    scheduler_manager.remove_schedule_job(schedule.id)

    return schedule


def resume_user_schedule(db: Session, user_id: int, schedule_id: int) -> Schedule:
    """Resumes a paused schedule and registers its APScheduler job."""
    schedule = get_user_schedule_by_id(db, user_id, schedule_id)

    validate_schedule_expression(schedule.schedule_type, schedule.schedule_expression)

    schedule.is_active = True
    schedule.next_run = calculate_next_run(schedule.schedule_type, schedule.schedule_expression)
    db.commit()
    db.refresh(schedule)

    scheduler_manager.add_or_update_schedule_job(schedule, trigger_scheduled_execution)

    return schedule
