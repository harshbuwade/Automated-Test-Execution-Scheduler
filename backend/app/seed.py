from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.enums import ExecutionStatus, ScheduleType, TestStatus, TriggerType
from app.models.execution import Execution
from app.models.schedule import Schedule
from app.models.test import Test
from app.models.user import User


def seed_demo_data(db: Session) -> None:
    """Populates the database with realistic demo entries for default user if database is empty."""
    demo_email = "demo@scheduler.local"
    demo_user = db.query(User).filter(User.email == demo_email).first()

    if not demo_user:
        demo_user = User(
            name="Default User",
            email=demo_email,
            password_hash=hash_password("DemoPassword123!"),
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

    # Check if demo user has any tests
    existing_tests_count = db.query(Test).filter(Test.user_id == demo_user.id).count()
    if existing_tests_count > 0:
        return  # Data already seeded

    # 1. Create Sample Test Definitions
    test1 = Test(
        user_id=demo_user.id,
        name="Sample Unit Test Suite",
        description="Executes standard assertions for utility functions and core business logic validation.",
        script_path="test_scripts/sample_test.py",
        framework="pytest",
        timeout=30,
        status=TestStatus.ACTIVE,
    )
    test2 = Test(
        user_id=demo_user.id,
        name="E2E Sanity Pass Suite",
        description="Validates end-to-end API connectivity and database state consistency.",
        script_path="test_scripts/sample_pass.py",
        framework="pytest",
        timeout=60,
        status=TestStatus.ACTIVE,
    )
    test3 = Test(
        user_id=demo_user.id,
        name="Regression Security & Edge Cases",
        description="Validates boundary conditions, rate limiting, and intentional failure handling.",
        script_path="test_scripts/sample_fail.py",
        framework="pytest",
        timeout=45,
        status=TestStatus.ACTIVE,
    )

    db.add_all([test1, test2, test3])
    db.commit()
    db.refresh(test1)
    db.refresh(test2)
    db.refresh(test3)

    # 2. Create Sample Schedules
    sched1 = Schedule(
        test_id=test1.id,
        schedule_type=ScheduleType.INTERVAL,
        schedule_expression="3600",
        is_active=True,
        next_run=datetime.now(timezone.utc) + timedelta(minutes=45),
        last_run=datetime.now(timezone.utc) - timedelta(minutes=15),
    )
    sched2 = Schedule(
        test_id=test3.id,
        schedule_type=ScheduleType.CRON,
        schedule_expression="0 0 * * *",
        is_active=True,
        next_run=datetime.now(timezone.utc) + timedelta(hours=8),
        last_run=datetime.now(timezone.utc) - timedelta(hours=16),
    )

    db.add_all([sched1, sched2])
    db.commit()
    db.refresh(sched1)
    db.refresh(sched2)

    # 3. Create Historical Executions
    now = datetime.now(timezone.utc)
    executions = [
        Execution(
            test_id=test1.id,
            schedule_id=sched1.id,
            status=ExecutionStatus.PASSED,
            trigger_type=TriggerType.SCHEDULED,
            started_at=now - timedelta(hours=4),
            finished_at=now - timedelta(hours=4) + timedelta(seconds=1, microseconds=420000),
            duration=1.42,
            exit_code=0,
            stdout="============================= test session starts =============================\nplatform win32 -- Python 3.14.3, pytest-9.1.1\ncollected 3 items\n\ntest_scripts/sample_test.py ... [100%]\n\n============================== 3 passed in 1.42s ==============================",
            stderr="",
        ),
        Execution(
            test_id=test2.id,
            schedule_id=None,
            status=ExecutionStatus.PASSED,
            trigger_type=TriggerType.MANUAL,
            started_at=now - timedelta(hours=3),
            finished_at=now - timedelta(hours=3) + timedelta(seconds=0, microseconds=580000),
            duration=0.58,
            exit_code=0,
            stdout="============================= test session starts =============================\nplatform win32 -- Python 3.14.3, pytest-9.1.1\ncollected 1 item\n\ntest_scripts/sample_pass.py . [100%]\n\n============================== 1 passed in 0.58s ==============================",
            stderr="",
        ),
        Execution(
            test_id=test3.id,
            schedule_id=sched2.id,
            status=ExecutionStatus.FAILED,
            trigger_type=TriggerType.SCHEDULED,
            started_at=now - timedelta(hours=2),
            finished_at=now - timedelta(hours=2) + timedelta(seconds=0, microseconds=890000),
            duration=0.89,
            exit_code=1,
            stdout="============================= test session starts =============================\nplatform win32 -- Python 3.14.3, pytest-9.1.1\ncollected 1 item\n\ntest_scripts/sample_fail.py F [100%]\n\n================================== FAILURES ==================================\n_________________________________ test_failure _________________________________\n    def test_failure():\n>       assert 1 == 2\nE       AssertionError: assert 1 == 2\n\n============================== 1 failed in 0.89s ==============================",
            stderr="FAILED test_scripts/sample_fail.py::test_failure - AssertionError: assert 1 == 2",
        ),
        Execution(
            test_id=test1.id,
            schedule_id=sched1.id,
            status=ExecutionStatus.PASSED,
            trigger_type=TriggerType.SCHEDULED,
            started_at=now - timedelta(hours=1),
            finished_at=now - timedelta(hours=1) + timedelta(seconds=1, microseconds=150000),
            duration=1.15,
            exit_code=0,
            stdout="============================= test session starts =============================\nplatform win32 -- Python 3.14.3, pytest-9.1.1\ncollected 3 items\n\ntest_scripts/sample_test.py ... [100%]\n\n============================== 3 passed in 1.15s ==============================",
            stderr="",
        ),
        Execution(
            test_id=test2.id,
            schedule_id=None,
            status=ExecutionStatus.PASSED,
            trigger_type=TriggerType.MANUAL,
            started_at=now - timedelta(minutes=15),
            finished_at=now - timedelta(minutes=15) + timedelta(seconds=0, microseconds=450000),
            duration=0.45,
            exit_code=0,
            stdout="============================= test session starts =============================\nplatform win32 -- Python 3.14.3, pytest-9.1.1\ncollected 1 item\n\ntest_scripts/sample_pass.py . [100%]\n\n============================== 1 passed in 0.45s ==============================",
            stderr="",
        ),
    ]

    db.add_all(executions)
    db.commit()
