"""Settings Pydantic schemas (v2)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SettingCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: str
    value_type: str = Field(default="string")
    description: str | None = None


class SettingUpdate(BaseModel):
    value: str
    description: str | None = None


class SettingResponse(BaseModel):
    id: UUID
    key: str
    value: str
    value_type: str
    description: Optional[str] = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
