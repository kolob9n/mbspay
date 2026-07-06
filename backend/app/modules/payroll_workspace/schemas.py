"""Payroll Workspace schemas — status and action results."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ModuleStatus(BaseModel):
    calendar: bool = False
    timesheets: bool = False
    kpi: bool = False
    payments: bool = False
    payroll: bool = False
    payslips: bool = False
    closed: bool = False


class WorkspaceError(BaseModel):
    code: str
    message: str
    module: str
    entity_id: Optional[str] = None


class WorkspaceStatusResponse(BaseModel):
    period_id: UUID
    period_label: str
    period_status: str
    modules: ModuleStatus
    errors: list[WorkspaceError] = []


class KPIIndicatorItem(BaseModel):
    id: UUID
    code: str
    name: str
    is_active: bool


class KPIStatusResponse(BaseModel):
    indicators: list[KPIIndicatorItem] = []
    period_id: UUID
    total_employees: int = 0
    calculated: int = 0
    errors: int = 0


class PaymentStatusResponse(BaseModel):
    period_id: UUID
    last_import_date: Optional[str] = None
    documents_count: int = 0
    total_amount: Decimal = Decimal("0")
    total_employees: int = 0


class PayrollStatusResponse(BaseModel):
    period_id: UUID
    has_active_run: bool = False
    run_status: Optional[str] = None
    run_id: Optional[UUID] = None
    total_accrued: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    total_balance: Decimal = Decimal("0")
    total_employees: int = 0


class ActionResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[dict] = None
