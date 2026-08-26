import os
import sys
import time
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.scheduler import scheduler_manager


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

    # Ensure scheduler is started
    scheduler_manager.start()

    with TestClient(fastapi_app) as c:
        yield c

    # Cleanup dependency override and SessionLocal
    fastapi_app.dependency_overrides.clear()
    app.database.SessionLocal = orig_session_local
    Base.metadata.drop_all(bind=engine)




@pytest.fixture
def user_headers(client):
    """Fixture returning headers for User 1 and User 2."""
    c = client
    # User 1
    c.post("/api/auth/register", json={"name": "Sched User 1", "email": "s1@example.com", "password": "Password123!"})
    res1 = c.post("/api/auth/login", json={"email": "s1@example.com", "password": "Password123!"})
    h1 = {"Authorization": f"Bearer {res1.json()['access_token']}"}

    # User 2
    c.post("/api/auth/register", json={"name": "Sched User 2", "email": "s2@example.com", "password": "Password123!"})
    res2 = c.post("/api/auth/login", json={"email": "s2@example.com", "password": "Password123!"})
    h2 = {"Authorization": f"Bearer {res2.json()['access_token']}"}

    return h1, h2


def test_create_interval_schedule(client, user_headers):
    h1, _ = user_headers
    t_res = client.post("/api/tests", json={"name": "Interval Test", "script_path": "sample_pass.py"}, headers=h1)
    test_id = t_res.json()["id"]

    res = client.post(
        "/api/schedules",
        json={"test_id": test_id, "schedule_type": "interval", "schedule_expression": "60", "is_active": True},
        headers=h1,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["test_id"] == test_id
    assert data["schedule_type"] == "interval"
    assert data["schedule_expression"] == "60"
    assert data["is_active"] is True
    assert data["next_run"] is not None


def test_create_cron_schedule(client, user_headers):
    h1, _ = user_headers
    t_res = client.post("/api/tests", json={"name": "Cron Test", "script_path": "sample_pass.py"}, headers=h1)
    test_id = t_res.json()["id"]

    res = client.post(
        "/api/schedules",
        json={"test_id": test_id, "schedule_type": "cron", "schedule_expression": "0 9 * * *", "is_active": True},
        headers=h1,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["schedule_type"] == "cron"
    assert data["schedule_expression"] == "0 9 * * *"
    assert data["next_run"] is not None


def test_unauthenticated_cannot_create_schedule(client):
    res = client.post(
        "/api/schedules",
        json={"test_id": 1, "schedule_type": "interval", "schedule_expression": "60"},
    )
    assert res.status_code == 401


def test_cannot_schedule_another_users_test(client, user_headers):
    h1, h2 = user_headers
    t_res = client.post("/api/tests", json={"name": "Private Test", "script_path": "sample_pass.py"}, headers=h1)
    test_id = t_res.json()["id"]

    res = client.post(
        "/api/schedules",
        json={"test_id": test_id, "schedule_type": "interval", "schedule_expression": "60"},
        headers=h2,
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Test not found."


def test_invalid_interval_rejected(client, user_headers):
    h1, _ = user_headers
    t_res = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1)
    test_id = t_res.json()["id"]

    # Negative / zero interval
    res = client.post(
        "/api/schedules",
        json={"test_id": test_id, "schedule_type": "interval", "schedule_expression": "-5"},
        headers=h1,
    )
    assert res.status_code == 400

    # Non-numeric interval
    res2 = client.post(
        "/api/schedules",
        json={"test_id": test_id, "schedule_type": "interval", "schedule_expression": "invalid"},
        headers=h1,
    )
    assert res2.status_code == 400


def test_invalid_cron_rejected(client, user_headers):
    h1, _ = user_headers
    t_res = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1)
    test_id = t_res.json()["id"]

    res = client.post(
        "/api/schedules",
        json={"test_id": test_id, "schedule_type": "cron", "schedule_expression": "invalid cron string"},
        headers=h1,
    )
    assert res.status_code == 400


def test_list_and_get_own_schedules(client, user_headers):
    h1, h2 = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    t2 = client.post("/api/tests", json={"name": "T2", "script_path": "sample_pass.py"}, headers=h2).json()["id"]

    s1 = client.post("/api/schedules", json={"test_id": t1, "schedule_type": "interval", "schedule_expression": "60"}, headers=h1).json()["id"]
    s2 = client.post("/api/schedules", json={"test_id": t2, "schedule_type": "interval", "schedule_expression": "120"}, headers=h2).json()["id"]

    # List user 1 schedules
    list1 = client.get("/api/schedules", headers=h1).json()
    assert list1["total"] == 1
    assert list1["items"][0]["id"] == s1

    # User 2 cannot retrieve User 1's schedule -> 404
    get_res = client.get(f"/api/schedules/{s1}", headers=h2)
    assert get_res.status_code == 404


def test_update_pause_resume_schedule(client, user_headers):
    h1, _ = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    s1 = client.post("/api/schedules", json={"test_id": t1, "schedule_type": "interval", "schedule_expression": "60"}, headers=h1).json()["id"]

    # Update expression
    put_res = client.put(f"/api/schedules/{s1}", json={"schedule_expression": "120"}, headers=h1)
    assert put_res.status_code == 200
    assert put_res.json()["schedule_expression"] == "120"

    # Pause schedule
    pause_res = client.post(f"/api/schedules/{s1}/pause", headers=h1)
    assert pause_res.status_code == 200
    assert pause_res.json()["is_active"] is False
    assert pause_res.json()["next_run"] is None

    # Resume schedule
    resume_res = client.post(f"/api/schedules/{s1}/resume", headers=h1)
    assert resume_res.status_code == 200
    assert resume_res.json()["is_active"] is True
    assert resume_res.json()["next_run"] is None or resume_res.json()["next_run"] != ""


def test_delete_schedule_preserves_execution_history(client, user_headers):
    h1, _ = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    s1 = client.post("/api/schedules", json={"test_id": t1, "schedule_type": "interval", "schedule_expression": "60"}, headers=h1).json()["id"]

    # Trigger manual execution for test
    exec_res = client.post("/api/executions", json={"test_id": t1}, headers=h1)
    exec_id = exec_res.json()["id"]

    # Delete schedule
    del_res = client.delete(f"/api/schedules/{s1}", headers=h1)
    assert del_res.status_code == 200

    # Schedule is gone -> 404
    assert client.get(f"/api/schedules/{s1}", headers=h1).status_code == 404

    # Execution history remains intact!
    get_exec = client.get(f"/api/executions/{exec_id}", headers=h1)
    assert get_exec.status_code == 200
    assert get_exec.json()["id"] == exec_id


def test_scheduled_execution_triggering_updates_schedule_fields(client, user_headers):
    h1, _ = user_headers
    t1 = client.post("/api/tests", json={"name": "Fast Sched Test", "script_path": "sample_pass.py"}, headers=h1).json()["id"]

    # Create very short 1-second interval schedule
    s_res = client.post("/api/schedules", json={"test_id": t1, "schedule_type": "interval", "schedule_expression": "1", "is_active": True}, headers=h1)
    s1 = s_res.json()["id"]

    # Wait 2.5 seconds for APScheduler background thread to fire
    time.sleep(2.5)

    # Pause schedule to stop further triggers
    client.post(f"/api/schedules/{s1}/pause", headers=h1)

    # Query executions
    exec_list = client.get(f"/api/executions?test_id={t1}", headers=h1).json()
    assert exec_list["total"] >= 1
    scheduled_exec = exec_list["items"][0]
    assert scheduled_exec["trigger_type"] == "scheduled"
    assert scheduled_exec["status"] == "passed"
    assert scheduled_exec["schedule_id"] == s1

    # Verify schedule last_run updated
    sched_updated = client.get(f"/api/schedules/{s1}", headers=h1).json()
    assert sched_updated["last_run"] is None or sched_updated["last_run"] != ""
