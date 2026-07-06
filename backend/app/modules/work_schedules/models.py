"""WorkSchedule SQLAlchemy model.

Пока график хранится одной записью.
Позже — полноценный конструктор смен.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel
from app.shared.mixins import TimestampMixin


class WorkSchedule(BaseModel, TimestampMixin):
    __tablename__ = "work_schedules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    working_days: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    working_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<WorkSchedule {self.name} ({self.working_days}d × {self.working_hours}h)>"
