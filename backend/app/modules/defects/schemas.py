"""Defect Pydantic schemas (v2)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---- DefectType ------------------------------------------------------------


class DefectTypeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    penalty_percent: Decimal = Field(default=Decimal("0.00"), max_digits=5, decimal_places=2)
    comment: str | None = None
    is_active: bool = True


class DefectTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    penalty_percent: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    comment: str | None = None
    is_active: bool | None = None


class DefectTypeResponse(BaseModel):
    id: UUID
    code: str
    name: str
    penalty_percent: Decimal
    comment: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ---- Defect ----------------------------------------------------------------


class DefectCreate(BaseModel):
    employee_id: UUID
    date: date
    defect_type_id: UUID
    description: str | None = None


class DefectUpdate(BaseModel):
    defect_type_id: UUID | None = None
    description: str | None = None


class DefectResponse(BaseModel):
    id: UUID
    employee_id: UUID
    date: date
    defect_type_id: UUID
    description: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DefectEmployeeSummary(BaseModel):
    employee_id: UUID
    total_defects: int
    by_type: dict[str, int] = {}  # defect_type_code → count
