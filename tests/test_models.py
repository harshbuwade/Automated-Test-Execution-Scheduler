import os
import sys
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import Base
from app.models import (
    User,
    Test,
    Schedule,
    Execution,
    TestStatus,
    ScheduleType,
    ExecutionStatus,
    TriggerType,
)


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database session isolated per test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_user_creation_and_unique_email(db_session):
    """Verify User model creation and unique email constraint enforcement."""
    user1 = User(
        name="Alice Tester",
        email="alice@example.com",
        password_hash="hashed_secret_123",
    )
    db_session.add(user1)
    db_session.commit()

    assert user1.id is not None
    assert user1.name == "Alice Tester"
    assert user1.email == "alice@example.com"
    assert isinstance(user1.created_at, datetime)

    # Duplicate email attempt should trigger IntegrityError
    duplicate_user = User(
        name="Bob Duplicate",
        email="alice@example.com",
        password_hash="hashed_secret_456",
    )
    db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_to_tests_relationship_and_cascade(db_session):
    """Verify User -> Tests relationship and cascade deletion."""
    user = User(name="Test Owner", email="owner@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    test1 = Test(
        user_id=user.id,
        name="Login Flow Automation",
        description="Automated E2E login verification",
        script_path="tests/e2e/test_login.py",
        framework="pytest",
        timeout=300,
        status=TestStatus.ACTIVE,
    )
    test2 = Test(
        user_id=user.id,
        name="API Health Test",
        script_path="tests/api/test_health.py",
        status=TestStatus.DRAFT,
    )
    db_session.add_all([test1, test2])
    db_session.commit()

    # Relationship verification
    assert len(user.tests) == 2
    assert test1.user.email == "owner@example.com"

    # Cascade deletion check: Deleting User should delete associated Tests
    db_session.delete(user)
    db_session.commit()

    remaining_tests = db_session.query(Test).all()
    assert len(remaining_tests) == 0


def test_test_to_schedules_relationship_and_cascade(db_session):
    """Verify Test -> Schedules relationship and cascade deletion."""
    user = User(name="Scheduler User", email="sched@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    test = Test(
        user_id=user.id,
        name="Scheduled Regression Test",
        script_path="tests/test_regression.py",
    )
    db_session.add(test)
    db_session.commit()

    schedule = Schedule(
        test_id=test.id,
        schedule_type=ScheduleType.CRON,
        schedule_expression="0 0 * * *",
        is_active=True,
    )
    db_session.add(schedule)
    db_session.commit()

    assert len(test.schedules) == 1
    assert schedule.test.name == "Scheduled Regression Test"

    # Deleting Test should cascade delete Schedule
    db_session.delete(test)
    db_session.commit()

    assert db_session.query(Schedule).count() == 0


def test_test_and_schedule_to_executions_relationship(db_session):
    """Verify Test & Schedule -> Executions relationship and nullable schedule_id."""
    user = User(name="Runner User", email="runner@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    test = Test(user_id=user.id, name="Runner Test", script_path="tests/test_run.py")
    db_session.add(test)
    db_session.commit()

    schedule = Schedule(
        test_id=test.id,
        schedule_type=ScheduleType.INTERVAL,
        schedule_expression="every 30m",
    )
    db_session.add(schedule)
    db_session.commit()

    # 1. Scheduled Execution (has schedule_id)
    scheduled_exec = Execution(
        test_id=test.id,
        schedule_id=schedule.id,
        status=ExecutionStatus.PASSED,
        trigger_type=TriggerType.SCHEDULED,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.45,
        exit_code=0,
        stdout="1 passed in 1.45s",
    )

    # 2. Manual Trigger Execution (nullable schedule_id = None)
    manual_exec = Execution(
        test_id=test.id,
        schedule_id=None,
        status=ExecutionStatus.RUNNING,
        trigger_type=TriggerType.MANUAL,
    )

    db_session.add_all([scheduled_exec, manual_exec])
    db_session.commit()

    # Relationship assertions
    assert len(test.executions) == 2
    assert scheduled_exec.schedule_id == schedule.id
    assert scheduled_exec.schedule.schedule_type == ScheduleType.INTERVAL
    assert manual_exec.schedule_id is None
    assert manual_exec.schedule is None

    # Deleting Schedule should set execution.schedule_id to None (SET NULL) instead of deleting Execution
    db_session.delete(schedule)
    db_session.commit()

    db_session.refresh(scheduled_exec)
    assert scheduled_exec.schedule_id is None
    assert db_session.query(Execution).count() == 2


def test_enums_and_timestamp_defaults(db_session):
    """Verify enum values and UTC timestamp handling."""
    user = User(name="Enum User", email="enum@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    test = Test(
        user_id=user.id,
        name="Enum Check Test",
        script_path="tests/test_enum.py",
        status=TestStatus.ARCHIVED,
    )
    db_session.add(test)
    db_session.commit()

    assert test.status == TestStatus.ARCHIVED
    assert test.created_at is not None
    assert test.updated_at is not None
