"""Base declarative model — every entity must inherit from this."""

import uuid
from typing import Annotated

from sqlalchemy import UUID
from sqlalchemy.orm import DeclarativeBase, mapped_column

# ---- Types ---------------------------------------------------------------
uuid_pk = Annotated[
    uuid.UUID,
    mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    ),
]


class Base(DeclarativeBase):
    """Root declarative base for all SQLAlchemy models."""

    type_annotation_map = {}


class BaseModel(Base):
    """Convenience base that every entity model should inherit from.

    Provides the ``id`` UUID primary key automatically.
    """

    __abstract__ = True

    id: uuid_pk  # type: ignore[valid-type]
