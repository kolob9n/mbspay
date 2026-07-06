"""Unified API response wrapper.

Every endpoint returns:
    {"success": true, "data": {...}, "message": null}

Errors are handled by the global exception handler and return:
    {"success": false, "data": null, "message": "..."}
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard envelope for all API responses."""

    success: bool
    data: T | None = None
    message: str | None = None

    @classmethod
    def ok(cls, data: T, message: str | None = None) -> "ApiResponse[T]":
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, message: str) -> "ApiResponse[None]":
        return cls(success=False, data=None, message=message)
