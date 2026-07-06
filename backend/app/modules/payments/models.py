"""Payments SQLAlchemy models — Payment document + PaymentItem lines."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
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


class PaymentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class PaymentType(str, enum.Enum):
    CARD = "CARD"
    CASH = "CASH"
    OTHER = "OTHER"


# ---- Models ---------------------------------------------------------------


class Payment(BaseModel, TimestampMixin):
    __tablename__ = "payments"

    number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    payroll_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_periods.id"), nullable=False, index=True
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", create_type=True),
        default=PaymentStatus.DRAFT,
        nullable=False,
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )

    # ---- Relationships -----------------------------------------------------
    items: Mapped[list["PaymentItem"]] = relationship(
        "PaymentItem", back_populates="payment", lazy="selectin",
        order_by="PaymentItem.employee_id",
    )
    payroll_period: Mapped["PayrollPeriod"] = relationship(
        "PayrollPeriod", lazy="joined", foreign_keys=[payroll_period_id]
    )

    def __repr__(self) -> str:
        return f"<Payment {self.number} [{self.status.value}]>"


class PaymentItem(BaseModel):
    __tablename__ = "payment_items"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType, name="payment_type", create_type=True),
        default=PaymentType.CARD,
        nullable=False,
    )
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ---- Relationships -----------------------------------------------------
    payment: Mapped["Payment"] = relationship("Payment", back_populates="items")
    employee: Mapped["Employee"] = relationship("Employee", lazy="joined")

    def __repr__(self) -> str:
        return f"<PaymentItem emp={self.employee_id} amount={self.amount}>"
