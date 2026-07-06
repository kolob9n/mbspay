"""AttendanceType SQLAlchemy model — reference dictionary."""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class AttendanceType(BaseModel):
    __tablename__ = "attendance_types"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_working_day: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    counts_for_experience: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#4CAF50", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AttendanceType {self.code} — {self.name}>"
