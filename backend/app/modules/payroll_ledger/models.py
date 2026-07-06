"""PayrollLedger SQLAlchemy model — immutable movement registry."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel

if TYPE_CHECKING:
    from app.modules.employees.models import Employee
    from app.modules.payroll_periods.models import PayrollPeriod


# ---- Enums ----------------------------------------------------------------


class DocumentType(str, enum.Enum):
    PAYMENT = "PAYMENT"
    PAYROLL = "PAYROLL"
    ADJUSTMENT = "ADJUSTMENT"
    IMPORT = "IMPORT"


class OperationType(str, enum.Enum):
    ACCRUAL = "ACCRUAL"       # + начисление
    PAYMENT = "PAYMENT"       # - выплата
    CORRECTION = "CORRECTION" # ± корректировка/сторно


# ---- Model ----------------------------------------------------------------


class PayrollLedgerEntry(BaseModel):
    """Immutable ledger entry. Never updated, never deleted.

    Balance = Σ(amount) for employee + period.
    """

    __tablename__ = "payroll_ledger"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    payroll_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_periods.id"), nullable=False, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="ledger_document_type", create_type=True),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    operation_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType, name="ledger_operation_type", create_type=True),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    operation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # ---- Relationships -----------------------------------------------------
    employee: Mapped["Employee"] = relationship("Employee", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<LedgerEntry emp={self.employee_id} "
            f"{self.operation_type.value} {self.amount}>"
        )
