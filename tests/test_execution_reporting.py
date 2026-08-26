from datetime import datetime, timedelta, timezone
import os
import sys
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.enums import ExecutionStatus, TriggerType
from app.models.execution import Execution
from app.models.schedule import Schedule
from app.models.test import Test
from app.models.user import User


@pytest.fixture(scope="function")
def client():
    """Create a TestClient with an isolated in-memory SQLite database using StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    import app.database
    orig_session_local = app.database.SessionLocal
    app.database.SessionLocal = TestingSessionLocal

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app) as c:
        c.TestingSessionLocal = TestingSessionLocal
        yield c

    fastapi_app.dependency_overrides.clear()
    app.database.SessionLocal = orig_session_local
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user_headers(client):
    """Fixture returning headers for User 1 and User 2."""
    c = client
    # User 1
    c.post("/api/auth/register", json={"name": "Report User 1", "email": "r1@example.com", "password": "Password123!"})
    res1 = c.post("/api/auth/login", json={"email": "r1@example.com", "password": "Password123!"})
    h1 = {"Authorization": f"Bearer {res1.json()['access_token']}"}

    # User 2
    c.post("/api/auth/register", json={"name": "Report User 2", "email": "r2@example.com", "password": "Password123!"})
    res2 = c.post("/api/auth/login", json={"email": "r2@example.com", "password": "Password123!"})
    h2 = {"Authorization": f"Bearer {res2.json()['access_token']}"}

    return h1, h2


def test_unauthenticated_user_cannot_access_reporting(client):
    assert client.get("/api/executions").status_code == 401
    assert client.get("/api/executions/recent").status_code == 401
    assert client.get("/api/executions/stats").status_code == 401


def test_zero_executions_statistics_handling(client, user_headers):
    h1, _ = user_headers
    res = client.get("/api/executions/stats", headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["total_executions"] == 0
    assert data["passed"] == 0
    assert data["failed"] == 0
    assert data["timeout"] == 0
    assert data["success_rate"] == 0.0
    assert data["average_duration"] == 0.0


def test_execution_history_list_excludes_logs(client, user_headers):
    h1, _ = user_headers
    t_res = client.post("/api/tests", json={"name": "Pass Test", "script_path": "sample_pass.py"}, headers=h1)
    test_id = t_res.json()["id"]

    client.post("/api/executions", json={"test_id": test_id}, headers=h1)

    res = client.get("/api/executions", headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert "stdout" not in item
    assert "stderr" not in item
    assert item["status"] == "passed"


def test_execution_detail_includes_logs_and_metadata(client, user_headers):
    h1, _ = user_headers
    t_res = client.post("/api/tests", json={"name": "Pass Test Meta", "script_path": "sample_pass.py"}, headers=h1)
    test_id = t_res.json()["id"]

    exec_res = client.post("/api/executions", json={"test_id": test_id}, headers=h1)
    exec_id = exec_res.json()["id"]

    detail_res = client.get(f"/api/executions/{exec_id}", headers=h1)
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["id"] == exec_id
    assert data["test_name"] == "Pass Test Meta"
    assert data["test_framework"] == "pytest"
    assert "stdout" in data
    assert "stderr" in data
    assert "passed" in data["stdout"].lower()


def test_test_and_schedule_specific_history(client, user_headers):
    h1, _ = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    t2 = client.post("/api/tests", json={"name": "T2", "script_path": "sample_fail.py"}, headers=h1).json()["id"]

    s1 = client.post("/api/schedules", json={"test_id": t1, "schedule_type": "interval", "schedule_expression": "60"}, headers=h1).json()["id"]

    # Manual execution for T1
    client.post("/api/executions", json={"test_id": t1}, headers=h1)
    # Manual execution for T2
    client.post("/api/executions", json={"test_id": t2}, headers=h1)

    # Test-specific history for T1
    th1 = client.get(f"/api/tests/{t1}/executions", headers=h1).json()
    assert th1["total"] == 1
    assert th1["items"][0]["test_id"] == t1

    # Schedule-specific history for S1 (0 because manual executions have schedule_id = null)
    sh1 = client.get(f"/api/schedules/{s1}/executions", headers=h1).json()
    assert sh1["total"] == 0


def test_recent_executions_endpoint(client, user_headers):
    h1, _ = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]

    for _ in range(3):
        client.post("/api/executions", json={"test_id": t1}, headers=h1)

    res = client.get("/api/executions/recent?limit=2", headers=h1)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2


def test_reporting_statistics_calculation(client, user_headers):
    h1, _ = user_headers
    db = client.TestingSessionLocal()
    u1 = db.query(User).filter(User.email == "r1@example.com").first()

    # Create dummy test
    test = Test(user_id=u1.id, name="Stat Test", script_path="sample_pass.py", framework="pytest")
    db.add(test)
    db.commit()
    db.refresh(test)

    now = datetime.now(timezone.utc)
    # 2 PASSED (durations 2.0, 4.0), 1 FAILED (duration 3.0), 1 TIMEOUT (duration 5.0)
    e1 = Execution(test_id=test.id, status=ExecutionStatus.PASSED, duration=2.0, trigger_type=TriggerType.MANUAL, created_at=now)
    e2 = Execution(test_id=test.id, status=ExecutionStatus.PASSED, duration=4.0, trigger_type=TriggerType.MANUAL, created_at=now)
    e3 = Execution(test_id=test.id, status=ExecutionStatus.FAILED, duration=3.0, trigger_type=TriggerType.MANUAL, created_at=now)
    e4 = Execution(test_id=test.id, status=ExecutionStatus.TIMEOUT, duration=5.0, trigger_type=TriggerType.MANUAL, created_at=now)
    db.add_all([e1, e2, e3, e4])
    db.commit()
    db.close()

    res = client.get("/api/executions/stats", headers=h1)
    assert res.status_code == 200
    data = res.json()

    assert data["total_executions"] == 4
    assert data["passed"] == 2
    assert data["failed"] == 1
    assert data["timeout"] == 1
    # success_rate = 2 passed / 4 completed * 100 = 50.0
    assert data["success_rate"] == 50.0
    # avg_dur = (2+4+3+5)/4 = 3.5
    assert data["average_duration"] == 3.5


def test_date_range_filtering_and_validation(client, user_headers):
    h1, _ = user_headers

    # Test invalid range date_from > date_to -> 400
    d_from = "2026-08-30T00:00:00Z"
    d_to = "2026-08-01T00:00:00Z"
    res_err = client.get(f"/api/executions?date_from={d_from}&date_to={d_to}", headers=h1)
    assert res_err.status_code == 400
    assert "date_from must be less than or equal to date_to" in res_err.json()["detail"]

    # Test stats invalid date range -> 400
    res_stats_err = client.get(f"/api/executions/stats?date_from={d_from}&date_to={d_to}", headers=h1)
    assert res_stats_err.status_code == 400


def test_user_ownership_isolation_on_reporting_endpoints(client, user_headers):
    h1, h2 = user_headers
    t1 = client.post("/api/tests", json={"name": "User 1 Test", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    s1 = client.post("/api/schedules", json={"test_id": t1, "schedule_type": "interval", "schedule_expression": "60"}, headers=h1).json()["id"]
    exec_id = client.post("/api/executions", json={"test_id": t1}, headers=h1).json()["id"]

    # User 2 attempts to get User 1's test execution history -> 404
    assert client.get(f"/api/tests/{t1}/executions", headers=h2).status_code == 404

    # User 2 attempts to get User 1's schedule execution history -> 404
    assert client.get(f"/api/schedules/{s1}/executions", headers=h2).status_code == 404

    # User 2 attempts to get User 1's execution detail -> 404
    assert client.get(f"/api/executions/{exec_id}", headers=h2).status_code == 404
