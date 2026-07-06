"""Formula SQLAlchemy model — stored calculation formulas."""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel
from app.shared.mixins import TimestampMixin


class Formula(BaseModel, TimestampMixin):
    __tablename__ = "formulas"

    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expression: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Formula {self.code} — {self.name}>"
