"""PayrollPeriod Pydantic schemas (v2)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.payroll_periods.models import PeriodStatus


# ---- Request schemas -------------------------------------------------------


class PayrollPeriodCreate(BaseModel):
    """Payload for creating a new payroll period."""

    year: int = Field(..., ge=2000, le=2100, examples=[2026])
    month: int = Field(..., ge=1, le=12, examples=[7])


class PayrollPeriodUpdate(BaseModel):
    """Payload for updating an existing period (status only)."""

    status: PeriodStatus


# ---- Response schemas ------------------------------------------------------


class PayrollPeriodResponse(BaseModel):
    """Public representation of a payroll period."""

    id: UUID
    year: int
    month: int
    status: PeriodStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    model_config = {"from_attributes": True}


class PayrollPeriodListResponse(BaseModel):
    """Wrapper for listing multiple periods."""

    items: list[PayrollPeriodResponse]
    total: int
