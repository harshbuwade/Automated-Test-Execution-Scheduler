from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import TestStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.schedule import Schedule
    from app.models.execution import Execution


class Test(Base):
    __tablename__ = "tests"
    __test__ = False

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script_path: Mapped[str] = mapped_column(String(512), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), default="pytest", nullable=False)
    timeout: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    status: Mapped[TestStatus] = mapped_column(
        Enum(TestStatus),
        default=TestStatus.ACTIVE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tests")
    schedules: Mapped[List["Schedule"]] = relationship(
        "Schedule",
        back_populates="test",
        cascade="all, delete-orphan",
    )
    executions: Mapped[List["Execution"]] = relationship(
        "Execution",
        back_populates="test",
        cascade="all, delete-orphan",
    )
