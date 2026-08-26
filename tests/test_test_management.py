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
from app.models.enums import TestStatus


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
def user_tokens(client):
    """Helper fixture creating User 1 and User 2 with auth headers."""
    c = client
    # Register User 1
    c.post("/api/auth/register", json={"name": "User One", "email": "u1@example.com", "password": "Password123!"})
    res1 = c.post("/api/auth/login", json={"email": "u1@example.com", "password": "Password123!"})
    token1 = res1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Register User 2
    c.post("/api/auth/register", json={"name": "User Two", "email": "u2@example.com", "password": "Password123!"})
    res2 = c.post("/api/auth/login", json={"email": "u2@example.com", "password": "Password123!"})
    token2 = res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    return headers1, headers2


def test_authenticated_user_can_create_test(client, user_tokens):
    headers1, _ = user_tokens
    payload = {
        "name": "Login API Test",
        "description": "Validates the login API endpoint",
        "script_path": "sample_test.py",
        "framework": "pytest",
        "timeout": 300,
    }
    response = client.post("/api/tests", json=payload, headers=headers1)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Login API Test"
    assert data["script_path"] == "test_scripts/sample_test.py"
    assert data["framework"] == "pytest"
    assert data["timeout"] == 300
    assert data["status"] == "active"
    assert "id" in data
    assert "user_id" in data


def test_unauthenticated_user_cannot_create_test(client):
    payload = {
        "name": "Unauth Test",
        "script_path": "sample_test.py",
    }
    response = client.post("/api/tests", json=payload)
    assert response.status_code == 401


def test_user_can_list_own_tests_and_isolation(client, user_tokens):
    headers1, headers2 = user_tokens

    # User 1 creates 2 tests
    client.post(
        "/api/tests",
        json={"name": "U1 Test 1", "script_path": "test_1.py"},
        headers=headers1,
    )
    client.post(
        "/api/tests",
        json={"name": "U1 Test 2", "script_path": "test_2.py"},
        headers=headers1,
    )

    # User 2 creates 1 test
    client.post(
        "/api/tests",
        json={"name": "U2 Test 1", "script_path": "test_u2.py"},
        headers=headers2,
    )

    # User 1 lists tests
    res1 = client.get("/api/tests", headers=headers1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 2
    assert len(data1["items"]) == 2
    names1 = [t["name"] for t in data1["items"]]
    assert "U1 Test 1" in names1
    assert "U1 Test 2" in names1
    assert "U2 Test 1" not in names1

    # User 2 lists tests
    res2 = client.get("/api/tests", headers=headers2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["name"] == "U2 Test 1"


def test_user_can_retrieve_own_test(client, user_tokens):
    headers1, _ = user_tokens
    create_res = client.post(
        "/api/tests",
        json={"name": "Get Test", "script_path": "get_test.py"},
        headers=headers1,
    )
    test_id = create_res.json()["id"]

    res = client.get(f"/api/tests/{test_id}", headers=headers1)
    assert res.status_code == 200
    assert res.json()["name"] == "Get Test"


def test_user_cannot_retrieve_another_users_test(client, user_tokens):
    headers1, headers2 = user_tokens
    create_res = client.post(
        "/api/tests",
        json={"name": "User 1 Secret Test", "script_path": "secret.py"},
        headers=headers1,
    )
    test_id = create_res.json()["id"]

    # User 2 attempts to get User 1's test -> 404 Not Found
    res = client.get(f"/api/tests/{test_id}", headers=headers2)
    assert res.status_code == 404
    assert res.json()["detail"] == "Test not found."


def test_user_can_update_own_test(client, user_tokens):
    headers1, _ = user_tokens
    create_res = client.post(
        "/api/tests",
        json={"name": "Original Name", "script_path": "original.py", "timeout": 120},
        headers=headers1,
    )
    test_id = create_res.json()["id"]

    update_payload = {
        "name": "Updated Name",
        "timeout": 600,
        "status": "inactive",
    }
    update_res = client.put(f"/api/tests/{test_id}", json=update_payload, headers=headers1)

    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "Updated Name"
    assert data["timeout"] == 600
    assert data["status"] == "inactive"
    assert data["script_path"] == "test_scripts/original.py"


def test_user_cannot_update_another_users_test(client, user_tokens):
    headers1, headers2 = user_tokens
    create_res = client.post(
        "/api/tests",
        json={"name": "U1 Test", "script_path": "u1.py"},
        headers=headers1,
    )
    test_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/tests/{test_id}",
        json={"name": "Hacked Name"},
        headers=headers2,
    )
    assert update_res.status_code == 404


def test_user_can_delete_own_test(client, user_tokens):
    headers1, _ = user_tokens
    create_res = client.post(
        "/api/tests",
        json={"name": "Delete Me", "script_path": "delete.py"},
        headers=headers1,
    )
    test_id = create_res.json()["id"]

    del_res = client.delete(f"/api/tests/{test_id}", headers=headers1)
    assert del_res.status_code == 200
    assert del_res.json()["detail"] == "Test deleted successfully."

    # Verify deleted
    get_res = client.get(f"/api/tests/{test_id}", headers=headers1)
    assert get_res.status_code == 404


def test_user_cannot_delete_another_users_test(client, user_tokens):
    headers1, headers2 = user_tokens
    create_res = client.post(
        "/api/tests",
        json={"name": "U1 Important Test", "script_path": "important.py"},
        headers=headers1,
    )
    test_id = create_res.json()["id"]

    del_res = client.delete(f"/api/tests/{test_id}", headers=headers2)
    assert del_res.status_code == 404

    # Verify test still exists for User 1
    get_res = client.get(f"/api/tests/{test_id}", headers=headers1)
    assert get_res.status_code == 200


def test_script_path_security_validations(client, user_tokens):
    headers, _ = user_tokens

    # 1. Absolute Windows path rejected
    res1 = client.post(
        "/api/tests",
        json={"name": "Absolute Win", "script_path": "C:\\Windows\\System32\\cmd.exe"},
        headers=headers,
    )
    assert res1.status_code == 422
    assert "Absolute script paths are strictly forbidden" in res1.text

    # 2. Absolute Unix path rejected
    res2 = client.post(
        "/api/tests",
        json={"name": "Absolute Unix", "script_path": "/etc/passwd"},
        headers=headers,
    )
    assert res2.status_code == 422
    assert "Absolute script paths are strictly forbidden" in res2.text

    # 3. Path traversal rejected
    res3 = client.post(
        "/api/tests",
        json={"name": "Traversal", "script_path": "../../../secret_key.py"},
        headers=headers,
    )
    assert res3.status_code == 422
    assert "Path traversal sequences" in res3.text

    # 4. Command injection characters rejected
    res4 = client.post(
        "/api/tests",
        json={"name": "Injection", "script_path": "test.py; rm -rf /"},
        headers=headers,
    )
    assert res4.status_code == 422
    assert "invalid security characters" in res4.text

    # 5. Unsupported extension rejected
    res5 = client.post(
        "/api/tests",
        json={"name": "Shell Script", "script_path": "exploit.sh"},
        headers=headers,
    )
    assert res5.status_code == 422
    assert "Only Python test scripts (.py) are currently supported" in res5.text


def test_timeout_and_framework_defaults_and_limits(client, user_tokens):
    headers, _ = user_tokens

    # 1. Default timeout and framework
    res1 = client.post(
        "/api/tests",
        json={"name": "Defaults Test", "script_path": "defaults.py"},
        headers=headers,
    )
    assert res1.status_code == 201
    assert res1.json()["framework"] == "pytest"
    assert res1.json()["timeout"] == 300

    # 2. Timeout too large (> 3600)
    res2 = client.post(
        "/api/tests",
        json={"name": "High Timeout", "script_path": "high.py", "timeout": 5000},
        headers=headers,
    )
    assert res2.status_code == 422

    # 3. Timeout too small (< 1)
    res3 = client.post(
        "/api/tests",
        json={"name": "Zero Timeout", "script_path": "zero.py", "timeout": 0},
        headers=headers,
    )
    assert res3.status_code == 422

    # 4. Unsupported framework rejected
    res4 = client.post(
        "/api/tests",
        json={"name": "Robot Test", "script_path": "robot.py", "framework": "unittest"},
        headers=headers,
    )
    assert res4.status_code == 422
    assert "Only 'pytest' framework is currently supported" in res4.text
