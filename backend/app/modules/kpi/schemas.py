"""KPI Pydantic schemas (v2)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.kpi.models import KPISource


# ---- Request schemas -------------------------------------------------------


class KPIIndicatorCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    formula_id: UUID
    weight: Decimal = Field(default=Decimal("1.00"), gt=0, max_digits=5, decimal_places=2)
    is_active: bool = True


class KPIIndicatorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    formula_id: UUID | None = None
    weight: Decimal | None = Field(None, gt=0, max_digits=5, decimal_places=2)
    is_active: bool | None = None


class KPIPeriodCreate(BaseModel):
    payroll_period_id: UUID
    indicator_id: UUID
    value: Decimal = Field(..., max_digits=12, decimal_places=4)
    comment: str | None = None


class KPIPeriodUpdate(BaseModel):
    value: Decimal | None = Field(None, max_digits=12, decimal_places=4)
    comment: str | None = None


class KPIEmployeeValueCreate(BaseModel):
    employee_id: UUID
    payroll_period_id: UUID
    indicator_id: UUID
    value: Decimal = Field(..., max_digits=12, decimal_places=4)
    source: KPISource = KPISource.MANUAL
    comment: str | None = None


# ---- Response schemas ------------------------------------------------------


class KPIIndicatorResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    formula_id: UUID
    weight: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KPIPeriodResponse(BaseModel):
    id: UUID
    payroll_period_id: UUID
    indicator_id: UUID
    value: Decimal
    comment: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KPIEmployeeValueResponse(BaseModel):
    id: UUID
    employee_id: UUID
    payroll_period_id: UUID
    indicator_id: UUID
    value: Decimal
    source: KPISource
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Calculation -----------------------------------------------------------


class KPIEmployeeResult(BaseModel):
    employee_id: UUID
    payroll_period_id: UUID
    results: dict[str, Decimal] = {}  # indicator_code → computed value
    total_kpi: Decimal = Decimal("0")
    details: list[dict] = []
