"""Payslip SQLAlchemy models — Payslip document + PayslipItem lines."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
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
    from app.modules.payroll.models import PayrollRun
    from app.modules.payroll_periods.models import PayrollPeriod


class PayslipStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    SIGNED = "SIGNED"
    ARCHIVED = "ARCHIVED"


class LineType(str, enum.Enum):
    BASE = "BASE"
    KPI = "KPI"
    OVERTIME = "OVERTIME"
    BONUS = "BONUS"
    ALLOWANCE = "ALLOWANCE"
    PENALTY = "PENALTY"
    PAYMENT = "PAYMENT"
    TOTAL = "TOTAL"


class Payslip(BaseModel, TimestampMixin):
    __tablename__ = "payslips"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_runs.id"), nullable=False, index=True
    )
    payroll_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_periods.id"), nullable=False, index=True
    )
    number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[PayslipStatus] = mapped_column(
        Enum(PayslipStatus, name="payslip_status", create_type=True),
        default=PayslipStatus.DRAFT, nullable=False
    )
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    items: Mapped[list["PayslipItem"]] = relationship("PayslipItem", back_populates="payslip", lazy="selectin", order_by="PayslipItem.sort_order")
    employee: Mapped["Employee"] = relationship("Employee", lazy="joined")
    payroll_run: Mapped["PayrollRun"] = relationship("PayrollRun", lazy="joined")

    def __repr__(self) -> str:
        return f"<Payslip {self.number} [{self.status.value}]>"


class PayslipItem(BaseModel):
    __tablename__ = "payslip_items"

    payslip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payslips.id"), nullable=False, index=True
    )
    line_type: Mapped[LineType] = mapped_column(
        Enum(LineType, name="payslip_line_type", create_type=True), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    payslip: Mapped["Payslip"] = relationship("Payslip", back_populates="items")

    def __repr__(self) -> str:
        return f"<PayslipItem {self.line_type.value} {self.amount}>"
