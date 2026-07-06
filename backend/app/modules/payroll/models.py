"""Payroll SQLAlchemy models — PayrollRun + PayrollResult."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel
from app.shared.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.modules.employees.models import Employee
    from app.modules.payroll_periods.models import PayrollPeriod


# ---- Enums ----------------------------------------------------------------


class PayrollRunStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


# ---- Models ---------------------------------------------------------------


class PayrollRun(BaseModel, TimestampMixin):
    """Document representing one payroll calculation run."""

    __tablename__ = "payroll_runs"

    number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    payroll_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_periods.id"), nullable=False, index=True
    )
    status: Mapped[PayrollRunStatus] = mapped_column(
        Enum(PayrollRunStatus, name="payroll_run_status", create_type=True),
        default=PayrollRunStatus.DRAFT,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    calculation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    formula_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # ---- Relationships -----------------------------------------------------
    results: Mapped[list["PayrollResult"]] = relationship(
        "PayrollResult", back_populates="payroll_run", lazy="selectin"
    )
    payroll_period: Mapped["PayrollPeriod"] = relationship(
        "PayrollPeriod", lazy="joined", foreign_keys=[payroll_period_id]
    )

    def __repr__(self) -> str:
        return f"<PayrollRun {self.number} v{self.version} [{self.status.value}]>"


class PayrollResult(BaseModel, TimestampMixin):
    """Per-employee calculation result with full formula snapshot."""

    __tablename__ = "payroll_results"

    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_runs.id"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )

    # ---- Inputs ------------------------------------------------------------
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    worked_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    worked_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    norm_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    norm_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ---- Computed ----------------------------------------------------------
    base_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    kpi: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    bonus: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    penalty: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    overtime: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    # ---- Audit -------------------------------------------------------------
    formula_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None
    )

    # ---- Relationships -----------------------------------------------------
    payroll_run: Mapped["PayrollRun"] = relationship(
        "PayrollRun", back_populates="results"
    )
    employee: Mapped["Employee"] = relationship("Employee", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<PayrollResult emp={self.employee_id} "
            f"total={self.total} balance={self.balance}>"
        )
