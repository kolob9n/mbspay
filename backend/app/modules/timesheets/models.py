"""Timesheet SQLAlchemy models — Timesheet and TimesheetEntry."""

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel
from app.shared.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.modules.attendance_types.models import AttendanceType
    from app.modules.departments.models import Department
    from app.modules.employees.models import Employee
    from app.modules.payroll_periods.models import PayrollPeriod


# ---- Enums ----------------------------------------------------------------


class TimesheetStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    RETURNED = "RETURNED"
    CLOSED = "CLOSED"


# ---- Models ---------------------------------------------------------------


class Timesheet(BaseModel, TimestampMixin):
    __tablename__ = "timesheets"

    payroll_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_periods.id"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    status: Mapped[TimesheetStatus] = mapped_column(
        Enum(TimesheetStatus, name="timesheet_status", create_type=True),
        default=TimesheetStatus.DRAFT,
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # ---- Relationships -----------------------------------------------------
    entries: Mapped[list["TimesheetEntry"]] = relationship(
        "TimesheetEntry", back_populates="timesheet", lazy="selectin",
        order_by="TimesheetEntry.date, TimesheetEntry.employee_id",
    )
    payroll_period: Mapped["PayrollPeriod"] = relationship(
        "PayrollPeriod", lazy="joined", foreign_keys=[payroll_period_id]
    )
    department: Mapped["Department"] = relationship(
        "Department", lazy="joined", foreign_keys=[department_id]
    )

    def __repr__(self) -> str:
        return (
            f"<Timesheet dept={self.department_id} "
            f"period={self.payroll_period_id} [{self.status.value}]>"
        )


class TimesheetEntry(BaseModel, TimestampMixin):
    __tablename__ = "timesheet_entries"

    __table_args__ = (
        UniqueConstraint(
            "timesheet_id", "employee_id", "date",
            name="uq_timesheet_entry_emp_date",
        ),
    )

    timesheet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("timesheets.id"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)

    attendance_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_types.id"), nullable=False
    )
    hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ---- Relationships -----------------------------------------------------
    timesheet: Mapped["Timesheet"] = relationship(
        "Timesheet", back_populates="entries"
    )
    employee: Mapped["Employee"] = relationship(
        "Employee", lazy="joined", foreign_keys=[employee_id]
    )
    attendance_type: Mapped["AttendanceType"] = relationship(
        "AttendanceType", lazy="joined", foreign_keys=[attendance_type_id]
    )

    def __repr__(self) -> str:
        return (
            f"<TimesheetEntry emp={self.employee_id} "
            f"date={self.date} hours={self.hours}>"
        )
