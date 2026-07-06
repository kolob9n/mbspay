"""WorkSchedule Pydantic schemas (v2)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WorkScheduleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    working_days: int = Field(default=5, ge=1, le=7)
    working_hours: int = Field(default=8, ge=1, le=24)


class WorkScheduleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    working_days: int | None = Field(None, ge=1, le=7)
    working_hours: int | None = Field(None, ge=1, le=24)
    is_active: bool | None = None


class WorkScheduleResponse(BaseModel):
    id: UUID
    name: str
    working_days: int
    working_hours: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
