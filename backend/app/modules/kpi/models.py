"""KPI SQLAlchemy models — KPIIndicator, KPIPeriod, KPIEmployeeValue."""

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
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
    from app.modules.formula_engine.models import Formula
    from app.modules.payroll_periods.models import PayrollPeriod


# ---- Enums ----------------------------------------------------------------


class KPISource(str, enum.Enum):
    MANUAL = "MANUAL"
    DEFECTS = "DEFECTS"
    TIMESHEET = "TIMESHEET"
    IMPORT = "IMPORT"
    SYSTEM = "SYSTEM"


# ---- Models ---------------------------------------------------------------


class KPIIndicator(BaseModel, TimestampMixin):
    __tablename__ = "kpi_indicators"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    formula_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("formulas.id"), nullable=False
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("1.00"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ---- Relationships -----------------------------------------------------
    formula: Mapped["Formula"] = relationship("Formula", lazy="joined")

    def __repr__(self) -> str:
        return f"<KPIIndicator {self.code} — {self.name}>"


class KPIPeriod(BaseModel, TimestampMixin):
    __tablename__ = "kpi_periods"

    payroll_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_periods.id"), nullable=False, index=True
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kpi_indicators.id"), nullable=False
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )

    # ---- Relationships -----------------------------------------------------
    indicator: Mapped["KPIIndicator"] = relationship("KPIIndicator", lazy="joined")
    payroll_period: Mapped["PayrollPeriod"] = relationship(
        "PayrollPeriod", lazy="joined", foreign_keys=[payroll_period_id]
    )

    def __repr__(self) -> str:
        return f"<KPIPeriod period={self.payroll_period_id} value={self.value}>"


class KPIEmployeeValue(BaseModel, TimestampMixin):
    __tablename__ = "kpi_employee_values"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    payroll_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_periods.id"), nullable=False, index=True
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kpi_indicators.id"), nullable=False
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    source: Mapped[KPISource] = mapped_column(
        Enum(KPISource, name="kpi_source", create_type=True),
        default=KPISource.SYSTEM,
        nullable=False,
    )
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ---- Relationships -----------------------------------------------------
    employee: Mapped["Employee"] = relationship("Employee", lazy="joined")
    indicator: Mapped["KPIIndicator"] = relationship("KPIIndicator", lazy="joined")
    payroll_period: Mapped["PayrollPeriod"] = relationship(
        "PayrollPeriod", lazy="joined", foreign_keys=[payroll_period_id]
    )

    def __repr__(self) -> str:
        return (
            f"<KPIEmployeeValue emp={self.employee_id} "
            f"indicator={self.indicator_id} value={self.value}>"
        )
