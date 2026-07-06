"""Employee Pydantic schemas (v2)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.departments.schemas import DepartmentResponse
from app.modules.employees.models import EmploymentType
from app.modules.positions.schemas import PositionResponse
from app.modules.work_schedules.schemas import WorkScheduleResponse


# ---- Request schemas -------------------------------------------------------


class EmployeeCreate(BaseModel):
    employee_number: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    department_id: UUID
    position_id: UUID
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    salary: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    work_schedule_id: UUID
    hire_date: date


class EmployeeUpdate(BaseModel):
    """employee_number is NOT included — cannot be changed after creation."""

    last_name: str | None = Field(None, min_length=1, max_length=100)
    first_name: str | None = Field(None, min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    department_id: UUID | None = None
    position_id: UUID | None = None
    employment_type: EmploymentType | None = None
    salary: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    work_schedule_id: UUID | None = None


class EmployeeDismiss(BaseModel):
    dismiss_date: date


# ---- Response schemas ------------------------------------------------------


class EmployeeResponse(BaseModel):
    id: UUID
    employee_number: str
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    full_name: str
    department_id: UUID
    position_id: UUID
    employment_type: EmploymentType
    salary: Decimal
    work_schedule_id: UUID
    is_active: bool
    hire_date: date
    dismiss_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EmployeeCardResponse(EmployeeResponse):
    """Extended employee view with resolved references."""

    department: Optional[DepartmentResponse] = None
    position: Optional[PositionResponse] = None
    work_schedule: Optional[WorkScheduleResponse] = None
