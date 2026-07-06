"""PayrollLedger Pydantic schemas (v2)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.modules.payroll_ledger.models import DocumentType, OperationType


class LedgerEntryResponse(BaseModel):
    id: UUID
    employee_id: UUID
    payroll_period_id: UUID
    document_type: DocumentType
    document_id: UUID
    operation_type: OperationType
    amount: Decimal
    operation_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeBalanceResponse(BaseModel):
    employee_id: UUID
    payroll_period_id: UUID
    accrued: Decimal = Decimal("0")
    paid: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")


class PeriodSummaryResponse(BaseModel):
    payroll_period_id: UUID
    total_accrued: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    total_balance: Decimal = Decimal("0")
    employee_count: int = 0
