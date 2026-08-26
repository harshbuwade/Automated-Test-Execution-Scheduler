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
from app.main import app


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

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user_headers(client):
    """Fixture returning headers for User 1 and User 2."""
    c = client
    # User 1
    c.post("/api/auth/register", json={"name": "Exec User 1", "email": "e1@example.com", "password": "Password123!"})
    res1 = c.post("/api/auth/login", json={"email": "e1@example.com", "password": "Password123!"})
    h1 = {"Authorization": f"Bearer {res1.json()['access_token']}"}

    # User 2
    c.post("/api/auth/register", json={"name": "Exec User 2", "email": "e2@example.com", "password": "Password123!"})
    res2 = c.post("/api/auth/login", json={"email": "e2@example.com", "password": "Password123!"})
    h2 = {"Authorization": f"Bearer {res2.json()['access_token']}"}

    return h1, h2


def test_authenticated_user_can_execute_passing_test(client, user_headers):
    h1, _ = user_headers
    # Register passing test
    t_res = client.post(
        "/api/tests",
        json={"name": "Pass Test", "script_path": "sample_pass.py", "timeout": 10},
        headers=h1,
    )
    test_id = t_res.json()["id"]

    # Trigger execution
    exec_res = client.post("/api/executions", json={"test_id": test_id}, headers=h1)
    assert exec_res.status_code == 201

    data = exec_res.json()
    assert data["test_id"] == test_id
    assert data["status"] == "passed"


    assert data["exit_code"] == 0
    assert data["trigger_type"] == "manual"
    assert "passed" in data["stdout"].lower()
    assert data["started_at"] is not None
    assert data["finished_at"] is not None
    assert data["duration"] >= 0.0


def test_unauthenticated_user_cannot_trigger_execution(client):
    response = client.post("/api/executions", json={"test_id": 1})
    assert response.status_code == 401


def test_user_cannot_execute_another_users_test(client, user_headers):
    h1, h2 = user_headers
    t_res = client.post(
        "/api/tests",
        json={"name": "U1 Private Test", "script_path": "sample_pass.py"},
        headers=h1,
    )
    test_id = t_res.json()["id"]

    # User 2 tries to execute User 1's test -> 404
    exec_res = client.post("/api/executions", json={"test_id": test_id}, headers=h2)
    assert exec_res.status_code == 404
    assert exec_res.json()["detail"] == "Test not found."


def test_failing_pytest_script_produces_failed_status(client, user_headers):
    h1, _ = user_headers
    t_res = client.post(
        "/api/tests",
        json={"name": "Fail Test", "script_path": "sample_fail.py", "timeout": 10},
        headers=h1,
    )
    test_id = t_res.json()["id"]

    exec_res = client.post("/api/executions", json={"test_id": test_id}, headers=h1)
    assert exec_res.status_code == 201

    data = exec_res.json()
    assert data["status"] == "failed"
    assert data["exit_code"] != 0
    assert "FAILED" in data["stdout"] or "failed" in data["stdout"].lower()


def test_timed_out_pytest_script_produces_timeout_status(client, user_headers):
    h1, _ = user_headers
    # Register test with short 2-second timeout
    t_res = client.post(
        "/api/tests",
        json={"name": "Timeout Test", "script_path": "sample_timeout.py", "timeout": 2},
        headers=h1,
    )
    test_id = t_res.json()["id"]

    exec_res = client.post("/api/executions", json={"test_id": test_id}, headers=h1)
    assert exec_res.status_code == 201

    data = exec_res.json()
    assert data["status"] == "timeout"
    assert data["exit_code"] == -1
    assert "timeout" in data["stderr"].lower()
    assert data["duration"] >= 1.5


def test_nonexistent_script_file_rejection(client, user_headers):
    h1, _ = user_headers
    t_res = client.post(
        "/api/tests",
        json={"name": "Missing File Test", "script_path": "non_existent_file.py"},
        headers=h1,
    )
    test_id = t_res.json()["id"]

    exec_res = client.post("/api/executions", json={"test_id": test_id}, headers=h1)
    assert exec_res.status_code == 201
    data = exec_res.json()
    assert data["status"] == "failed"
    assert "not found" in data["stderr"].lower()



def test_list_executions_returns_only_user_executions(client, user_headers):
    h1, h2 = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    t2 = client.post("/api/tests", json={"name": "T2", "script_path": "sample_pass.py"}, headers=h2).json()["id"]

    client.post("/api/executions", json={"test_id": t1}, headers=h1)
    client.post("/api/executions", json={"test_id": t2}, headers=h2)

    list1 = client.get("/api/executions", headers=h1).json()
    assert list1["total"] == 1
    assert list1["items"][0]["test_id"] == t1

    list2 = client.get("/api/executions", headers=h2).json()
    assert list2["total"] == 1
    assert list2["items"][0]["test_id"] == t2


def test_user_cannot_retrieve_another_users_execution(client, user_headers):
    h1, h2 = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    exec_id = client.post("/api/executions", json={"test_id": t1}, headers=h1).json()["id"]

    # User 2 attempts to get User 1's execution -> 404
    get_res = client.get(f"/api/executions/{exec_id}", headers=h2)
    assert get_res.status_code == 404


def test_executions_pagination_and_filtering(client, user_headers):
    h1, _ = user_headers
    t1 = client.post("/api/tests", json={"name": "T1", "script_path": "sample_pass.py"}, headers=h1).json()["id"]
    t2 = client.post("/api/tests", json={"name": "T2", "script_path": "sample_fail.py"}, headers=h1).json()["id"]

    client.post("/api/executions", json={"test_id": t1}, headers=h1)
    client.post("/api/executions", json={"test_id": t2}, headers=h1)

    # Filter by status=passed
    res_passed = client.get("/api/executions?status=passed", headers=h1)
    assert res_passed.status_code == 200
    assert res_passed.json()["total"] == 1
    assert res_passed.json()["items"][0]["status"] == "passed"

    # Filter by test_id=t2
    res_t2 = client.get(f"/api/executions?test_id={t2}", headers=h1)
    assert res_t2.status_code == 200
    assert res_t2.json()["total"] == 1
    assert res_t2.json()["items"][0]["status"] == "failed"
