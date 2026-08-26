from datetime import timedelta
import os
import sys
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.security import create_access_token, verify_password
from app.database import Base, get_db
from app.main import app
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

    # Create tables in in-memory database
    Base.metadata.create_all(bind=engine)


    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c, TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_successful_user_registration(client):
    c, TestingSessionLocal = client
    payload = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "password": "Password123!",
    }
    response = c.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Developer"
    assert data["email"] == "jane@example.com"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email_registration_rejection(client):
    c, TestingSessionLocal = client
    payload = {
        "name": "Jane Developer",
        "email": "Jane@Example.com",
        "password": "Password123!",
    }
    c.post("/api/auth/register", json=payload)

    # Attempt duplicate registration with different case
    response = c.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_password_stored_as_hash_never_plaintext(client):
    c, TestingSessionLocal = client
    raw_password = "MySecurePassword2026"
    payload = {
        "name": "Security Test User",
        "email": "security@example.com",
        "password": raw_password,
    }
    c.post("/api/auth/register", json=payload)

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "security@example.com").first()
    db.close()

    assert user is not None
    assert user.password_hash != raw_password
    assert not user.password_hash.startswith("MySecure")
    assert verify_password(raw_password, user.password_hash) is True


def test_successful_login(client):
    c, TestingSessionLocal = client
    c.post(
        "/api/auth/register",
        json={"name": "Bob Tester", "email": "bob@example.com", "password": "SecretPassword1"},
    )

    login_payload = {"email": "bob@example.com", "password": "SecretPassword1"}
    response = c.post("/api/auth/login", json=login_payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_invalid_password(client):
    c, TestingSessionLocal = client
    c.post(
        "/api/auth/register",
        json={"name": "Alice Smith", "email": "alice@example.com", "password": "CorrectPassword1"},
    )

    response = c.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_invalid_email_or_nonexistent_user(client):
    c, TestingSessionLocal = client
    response = c.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "SomePassword1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_get_me_with_valid_jwt(client):
    c, TestingSessionLocal = client
    reg_resp = c.post(
        "/api/auth/register",
        json={"name": "Me User", "email": "me@example.com", "password": "Password123"},
    )
    user_id = reg_resp.json()["id"]

    login_resp = c.post(
        "/api/auth/login",
        json={"email": "me@example.com", "password": "Password123"},
    )
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = c.get("/api/auth/me", headers=headers)

    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == "me@example.com"
    assert me_data["name"] == "Me User"


def test_get_me_without_token(client):
    c, TestingSessionLocal = client
    response = c.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication token is missing."


def test_get_me_invalid_jwt(client):
    c, TestingSessionLocal = client
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = c.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token."


def test_get_me_expired_jwt(client):
    c, TestingSessionLocal = client
    reg_resp = c.post(
        "/api/auth/register",
        json={"name": "Expired User", "email": "expired@example.com", "password": "Password123"},
    )
    user_id = reg_resp.json()["id"]

    # Generate token that expired 10 minutes ago
    expired_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(minutes=-10),
    )

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = c.get("/api/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication token has expired."
