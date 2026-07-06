"""Payment Pydantic schemas (v2)."""

from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.payments.models import PaymentStatus, PaymentType


# ---- Request schemas -------------------------------------------------------


class PaymentItemCreate(BaseModel):
    employee_id: UUID
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    payment_type: PaymentType = PaymentType.CARD
    comment: str | None = None


class PaymentCreate(BaseModel):
    number: str = Field(..., min_length=1, max_length=50)
    date: date_type
    payroll_period_id: UUID
    comment: str | None = None
    items: list[PaymentItemCreate] = Field(..., min_length=1)


class PaymentUpdate(BaseModel):
    date: date_type | None = None
    comment: str | None = None


# ---- Response schemas ------------------------------------------------------


class PaymentItemResponse(BaseModel):
    id: UUID
    payment_id: UUID
    employee_id: UUID
    amount: Decimal
    payment_type: PaymentType
    comment: Optional[str] = None

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: UUID
    number: str
    date: date_type
    payroll_period_id: UUID
    status: PaymentStatus
    comment: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_amount: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


class PaymentDetailResponse(PaymentResponse):
    items: list[PaymentItemResponse] = []


# ---- Import -----------------------------------------------------------------


class PaymentImportRow(BaseModel):
    employee_number: str | None = None
    employee_name: str | None = None
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)


class PaymentImportResult(BaseModel):
    document_id: UUID
    rows_imported: int
    rows_skipped: int
    errors: list[str] = []
