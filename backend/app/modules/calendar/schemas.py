"""Calendar Pydantic schemas (v2)."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.calendar.models import DayType, YearStatus


# ---- Request schemas -------------------------------------------------------


class CalendarYearCreate(BaseModel):
    year: int = Field(..., ge=2000, le=2100, examples=[2027])


class CalendarDayUpdate(BaseModel):
    day_type: DayType | None = None
    is_working_day: bool | None = None
    working_hours: int | None = Field(None, ge=0, le=24)
    comment: str | None = Field(None, max_length=500)


# ---- Response schemas ------------------------------------------------------


class CalendarYearSummaryResponse(BaseModel):
    id: UUID
    year: int
    status: YearStatus
    total_days: int = 0
    working_days_count: int = 0
    working_hours_total: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CalendarDayResponse(BaseModel):
    id: UUID
    calendar_year_id: UUID
    date: date
    day_type: DayType
    is_working_day: bool
    working_hours: int
    comment: Optional[str] = None

    model_config = {"from_attributes": True}


class MonthNormResponse(BaseModel):
    year: int
    month: int
    working_days: int
    working_hours: int


class CalendarMonthResponse(BaseModel):
    year: int
    month: int
    status: YearStatus
    days: list[CalendarDayResponse]
    norm: MonthNormResponse


class CalendarYearDetailResponse(BaseModel):
    id: UUID
    year: int
    status: YearStatus
    total_days: int
    working_days_count: int
    working_hours_total: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    days: list[CalendarDayResponse] = []

    model_config = {"from_attributes": True}
