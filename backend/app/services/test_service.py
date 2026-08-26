import math
from datetime import datetime, timezone
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.test import Test
from app.schemas.test import TestCreate, TestUpdate


def create_test(db: Session, user_id: int, test_in: TestCreate) -> Test:
    """Creates a new automated test script definition owned by user_id."""
    test = Test(
        user_id=user_id,
        name=test_in.name,
        description=test_in.description,
        script_path=test_in.script_path,
        framework=test_in.framework,
        timeout=test_in.timeout,
        status=test_in.status,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


def list_user_tests(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
) -> Tuple[List[Test], int, int]:
    """Retrieves paginated list of tests belonging ONLY to user_id.

    Returns:
        Tuple[List[Test], total_count, total_pages]
    """
    query = db.query(Test).filter(Test.user_id == user_id)
    total_count = query.with_entities(func.count(Test.id)).scalar() or 0

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    offset = (page - 1) * page_size

    items = query.order_by(Test.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total_count, total_pages


def get_user_test_by_id(db: Session, user_id: int, test_id: int) -> Test:
    """Retrieves a single test by ID ensuring ownership by user_id.

    Raises HTTP 404 if test does not exist OR belongs to another user.
    """
    test = db.query(Test).filter(Test.id == test_id, Test.user_id == user_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found.",
        )
    return test


def update_user_test(
    db: Session,
    user_id: int,
    test_id: int,
    test_in: TestUpdate,
) -> Test:
    """Updates an existing test definition owned by user_id."""
    test = get_user_test_by_id(db, user_id, test_id)

    update_data = test_in.model_dump(exclude_unset=True)
    if not update_data:
        return test

    for field, value in update_data.items():
        setattr(test, field, value)

    test.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(test)
    return test


def delete_user_test(db: Session, user_id: int, test_id: int) -> None:
    """Deletes a test definition owned by user_id."""
    test = get_user_test_by_id(db, user_id, test_id)
    db.delete(test)
    db.commit()
