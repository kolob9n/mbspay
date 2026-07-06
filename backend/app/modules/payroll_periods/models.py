"""PayrollPeriod SQLAlchemy model."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel
from app.shared.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    pass  # future relationships


class PeriodStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CALCULATED = "CALCULATED"
    CLOSED = "CLOSED"


class PayrollPeriod(BaseModel, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "payroll_periods"

    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_payroll_period_year_month"),
    )

    # ---- Business columns --------------------------------------------------
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[PeriodStatus] = mapped_column(
        Enum(PeriodStatus, name="period_status", create_type=True),
        default=PeriodStatus.OPEN,
        nullable=False,
    )

    # ---- Audit columns -----------------------------------------------------
    opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )

    # ---- Helpers -----------------------------------------------------------
    @property
    def period_label(self) -> str:
        return f"{self.year}-{self.month:02d}"

    def __repr__(self) -> str:
        return f"<PayrollPeriod {self.period_label} [{self.status.value}]>"
