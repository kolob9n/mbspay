"""AttendanceType Pydantic schemas (v2)."""

from uuid import UUID

from pydantic import BaseModel, Field


class AttendanceTypeResponse(BaseModel):
    id: UUID
    code: str
    name: str
    is_working_day: bool
    is_paid: bool
    counts_for_experience: bool
    default_hours: int
    color: str
    is_active: bool

    model_config = {"from_attributes": True}


class AttendanceTypeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    is_working_day: bool = True
    is_paid: bool = True
    counts_for_experience: bool = True
    default_hours: int = Field(default=8, ge=0, le=24)
    color: str = Field(default="#4CAF50", max_length=20)
    is_active: bool = True


class AttendanceTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    is_working_day: bool | None = None
    is_paid: bool | None = None
    counts_for_experience: bool | None = None
    default_hours: int | None = Field(None, ge=0, le=24)
    color: str | None = Field(None, max_length=20)
    is_active: bool | None = None
