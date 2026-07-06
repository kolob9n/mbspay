"""Calendar SQLAlchemy models — CalendarYear and CalendarDay."""

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel
from app.shared.mixins import TimestampMixin

if TYPE_CHECKING:
    pass


# ---- Enums ----------------------------------------------------------------


class YearStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"


class DayType(str, enum.Enum):
    WORKDAY = "WORKDAY"
    WEEKEND = "WEEKEND"
    HOLIDAY = "HOLIDAY"
    SHORT_DAY = "SHORT_DAY"
    CUSTOM = "CUSTOM"


# ---- Models ---------------------------------------------------------------


class CalendarYear(BaseModel, TimestampMixin):
    __tablename__ = "calendar_years"

    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    status: Mapped[YearStatus] = mapped_column(
        Enum(YearStatus, name="year_status", create_type=True),
        default=YearStatus.DRAFT,
        nullable=False,
    )

    # ---- Relationships -----------------------------------------------------
    days: Mapped[list["CalendarDay"]] = relationship(
        "CalendarDay",
        back_populates="calendar_year",
        lazy="selectin",
        order_by="CalendarDay.date",
    )

    def __repr__(self) -> str:
        return f"<CalendarYear {self.year} [{self.status.value}]>"


class CalendarDay(BaseModel, TimestampMixin):
    __tablename__ = "calendar_days"

    __table_args__ = (
        UniqueConstraint("calendar_year_id", "date", name="uq_calendar_day_year_date"),
    )

    # ---- Foreign key -------------------------------------------------------
    calendar_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calendar_years.id"), nullable=False, index=True
    )

    # ---- Day data ----------------------------------------------------------
    date: Mapped[date] = mapped_column(Date, nullable=False)
    day_type: Mapped[DayType] = mapped_column(
        Enum(DayType, name="day_type", create_type=True),
        default=DayType.WORKDAY,
        nullable=False,
    )
    is_working_day: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    working_hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ---- Relationships -----------------------------------------------------
    calendar_year: Mapped["CalendarYear"] = relationship(
        "CalendarYear", back_populates="days"
    )

    def __repr__(self) -> str:
        return (
            f"<CalendarDay {self.date} [{self.day_type.value}] "
            f"{self.working_hours}h>"
        )
