"""Payslip Pydantic schemas (v2)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.payslips.models import LineType, PayslipStatus


class PayslipItemResponse(BaseModel):
    id: UUID
    line_type: LineType
    title: str
    formula: str | None = None
    amount: Decimal
    sort_order: int
    model_config = {"from_attributes": True}


class PayslipResponse(BaseModel):
    id: UUID
    employee_id: UUID
    payroll_run_id: UUID
    payroll_period_id: UUID
    number: str
    status: PayslipStatus
    generated_at: datetime | None = None
    generated_by: UUID | None = None
    created_at: datetime
    items: list[PayslipItemResponse] = []
    model_config = {"from_attributes": True}


class PayslipDetailResponse(PayslipResponse):
    employee_name: str = ""
    employee_number: str = ""
    department_name: str = ""
    position_name: str = ""
    period_label: str = ""
    run_version: int = 1
    total_accrued: Decimal = Decimal("0")
    total_deducted: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    to_pay: Decimal = Decimal("0")
