from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserRegisterRequest


def register_new_user(db: Session, request: UserRegisterRequest) -> User:
    """Registers a new user after validating email uniqueness and hashing password."""
    normalized_email = request.email.lower().strip()

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Hash password securely
    hashed_password = hash_password(request.password)

    user = User(
        name=request.name.strip(),
        email=normalized_email,
        password_hash=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticates a user by email and password.

    Returns:
        User: Authenticated User object.

    Raises:
        HTTPException 401: Generic error on invalid email or password.
    """
    normalized_email = email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
