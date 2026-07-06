"""Formula Pydantic schemas (v2)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Request schemas -------------------------------------------------------


class FormulaCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    expression: str = Field(..., min_length=1)
    is_active: bool = True


class FormulaUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    expression: str | None = Field(None, min_length=1)
    is_active: bool | None = None


# ---- Evaluate / Validate ---------------------------------------------------


class EvaluateRequest(BaseModel):
    formula: str = Field(..., min_length=1, description="Expression string")
    variables: dict[str, int | float] = Field(
        default_factory=dict,
        description="Variable name → numeric value",
    )


class EvaluateResponse(BaseModel):
    result: Decimal


class ValidateRequest(BaseModel):
    formula: str = Field(..., min_length=1, description="Expression to validate")


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    variables: list[str] = []


# ---- Response schemas ------------------------------------------------------


class FormulaResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    expression: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
