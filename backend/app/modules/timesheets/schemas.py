"""Timesheet Pydantic schemas (v2)."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.timesheets.models import TimesheetStatus


# ---- Request schemas -------------------------------------------------------


class TimesheetCreate(BaseModel):
    payroll_period_id: UUID
    department_id: UUID


class TimesheetEntryUpdate(BaseModel):
    attendance_type_id: UUID | None = None
    hours: int | None = Field(None, ge=0, le=24)
    comment: str | None = Field(None, max_length=500)


# ---- Response schemas ------------------------------------------------------


class TimesheetResponse(BaseModel):
    id: UUID
    payroll_period_id: UUID
    department_id: UUID
    status: TimesheetStatus
    created_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TimesheetEntryResponse(BaseModel):
    id: UUID
    timesheet_id: UUID
    employee_id: UUID
    date: date
    attendance_type_id: UUID
    hours: int
    comment: Optional[str] = None

    model_config = {"from_attributes": True}


# ---- Matrix view -----------------------------------------------------------


class MatrixDayItem(BaseModel):
    day: int
    date: date
    type_code: str = ""
    type_name: str = ""
    hours: int = 0
    color: str = ""
    comment: Optional[str] = None


class MatrixEmployeeRow(BaseModel):
    employee_id: UUID
    employee_number: str
    full_name: str
    position_name: str = ""
    days: list[MatrixDayItem] = []


class TimesheetMatrixResponse(BaseModel):
    timesheet_id: UUID
    year: int
    month: int
    department_name: str = ""
    status: TimesheetStatus
    total_employees: int
    total_days: int
    employees: list[MatrixEmployeeRow] = []


# ---- Summary ---------------------------------------------------------------


class TimesheetSummaryResponse(BaseModel):
    worked_days: int = 0
    worked_hours: int = 0
    vacation_days: int = 0
    sick_days: int = 0
    overtime_hours: int = 0
    absence_days: int = 0
    business_trip_days: int = 0


# ---- Detail (with entries) -------------------------------------------------


class TimesheetDetailResponse(TimesheetResponse):
    entries: list[TimesheetEntryResponse] = []
