"""Settings SQLAlchemy model — key-value configuration store."""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class Setting(BaseModel):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(
        String(50), default="string", nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Setting {self.key}={self.value}>"
