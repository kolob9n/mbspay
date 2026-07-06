"""Workflow SQLAlchemy model — transition definitions."""

from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class WorkflowTransition(BaseModel):
    """Defines one allowed state transition for a document type."""

    __tablename__ = "workflow_transitions"

    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    from_state: Mapped[str] = mapped_column(String(50), nullable=False)
    to_state: Mapped[str] = mapped_column(String(50), nullable=False)
    permission: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowTransition {self.document_type}: "
            f"{self.from_state} → {self.to_state}>"
        )
