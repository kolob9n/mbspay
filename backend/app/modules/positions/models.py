"""Position SQLAlchemy model."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel
from app.shared.mixins import TimestampMixin


class Position(BaseModel, TimestampMixin):
    __tablename__ = "positions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Position {self.code} — {self.name}>"
