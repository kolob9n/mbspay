"""Employee SQLAlchemy domain model."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel
from app.shared.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.modules.departments.models import Department
    from app.modules.positions.models import Position
    from app.modules.work_schedules.models import WorkSchedule


class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"


class Employee(BaseModel, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "employees"

    # ---- Identification ----------------------------------------------------
    employee_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ---- Employment details ------------------------------------------------
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="employment_type", create_type=True),
        default=EmploymentType.FULL_TIME,
        nullable=False,
    )
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    work_schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_schedules.id"), nullable=False
    )

    # ---- Status ------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    dismiss_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ---- Relationships (eager-load references) -----------------------------
    department: Mapped["Department"] = relationship(
        "Department", lazy="joined", foreign_keys=[department_id]
    )
    position: Mapped["Position"] = relationship(
        "Position", lazy="joined", foreign_keys=[position_id]
    )
    work_schedule: Mapped["WorkSchedule"] = relationship(
        "WorkSchedule", lazy="joined", foreign_keys=[work_schedule_id]
    )

    # ---- Future relationships (placeholders) -------------------------------
    # payroll_items: Mapped[list["PayrollItem"]] = relationship(...)
    # timesheets: Mapped[list["Timesheet"]] = relationship(...)
    # payments: Mapped[list["Payment"]] = relationship(...)
    # defects: Mapped[list["Defect"]] = relationship(...)

    # ---- Computed properties -----------------------------------------------
    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def __repr__(self) -> str:
        return f"<Employee {self.employee_number} — {self.full_name}>"
