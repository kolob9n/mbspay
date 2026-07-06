"""Payroll Pydantic schemas (v2)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.payroll.models import PayrollRunStatus


# ---- Request schemas -------------------------------------------------------


class PayrollRunCreate(BaseModel):
    payroll_period_id: UUID


# ---- Response schemas ------------------------------------------------------


class PayrollRunResponse(BaseModel):
    id: UUID
    number: str
    payroll_period_id: UUID
    status: PayrollRunStatus
    version: int
    calculation_date: Optional[datetime] = None
    formula_version: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PayrollResultResponse(BaseModel):
    id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    salary: Decimal
    worked_days: int
    worked_hours: int
    norm_days: int
    norm_hours: int
    base_salary: Decimal
    kpi: Decimal
    bonus: Decimal
    penalty: Decimal
    overtime: Decimal
    paid: Decimal
    total: Decimal
    balance: Decimal
    formula_snapshot: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PayrollRunDetailResponse(PayrollRunResponse):
    results: list[PayrollResultResponse] = []
    employee_count: int = 0
    total_amount: Decimal = Decimal("0")


# ---- Payslip ---------------------------------------------------------------


class PayslipResponse(BaseModel):
    employee_id: UUID
    employee_name: str = ""
    employee_number: str = ""
    payroll_run_id: UUID
    period_label: str = ""
    salary: Decimal = Decimal("0")
    worked_days: int = 0
    norm_days: int = 0
    base_salary: Decimal = Decimal("0")
    kpi: Decimal = Decimal("0")
    bonus: Decimal = Decimal("0")
    penalty: Decimal = Decimal("0")
    overtime: Decimal = Decimal("0")
    paid: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")
    to_pay: Decimal = Decimal("0")  # total - paid
