"""Pagination helpers — reusable params and response model."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query-string pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")


class Page(BaseModel, Generic[T]):
    """Internal pagination result."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated API response."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
