from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import ExecutionStatus, TriggerType

if TYPE_CHECKING:
    from app.models.test import Test
    from app.models.schedule import Schedule


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    test_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schedule_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    test: Mapped["Test"] = relationship("Test", back_populates="executions")
    schedule: Mapped[Optional["Schedule"]] = relationship("Schedule", back_populates="executions")
