"""Domain-level exceptions for the entire application."""

from http import HTTPStatus


class AppException(Exception):
    """Base application exception with HTTP status code."""

    status: int = HTTPStatus.INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundException(AppException):
    status = HTTPStatus.NOT_FOUND
    detail = "Resource not found"


class ConflictException(AppException):
    status = HTTPStatus.CONFLICT
    detail = "Resource conflict"


class BusinessRuleException(AppException):
    status = HTTPStatus.UNPROCESSABLE_ENTITY
    detail = "Business rule violation"
