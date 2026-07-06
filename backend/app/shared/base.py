"""Base declarative model — every entity must inherit from this."""

import uuid

from sqlalchemy import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base for all SQLAlchemy models."""

    type_annotation_map = {}


class BaseModel(Base):
    """Convenience base that every entity model should inherit from.

    Provides the ``id`` UUID primary key automatically.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
