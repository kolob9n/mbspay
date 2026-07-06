"""Calendar API — HTTP layer.

Thin layer: receives request → calls Service → wraps in ApiResponse.
No business logic, no SQLAlchemy.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.calendar.schemas import (
    CalendarDayResponse,
    CalendarDayUpdate,
    CalendarMonthResponse,
    CalendarYearCreate,
    CalendarYearDetailResponse,
    CalendarYearSummaryResponse,
    MonthNormResponse,
)
from app.modules.calendar.service import CalendarService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/calendar", tags=["Calendar"])


# ---- Dependency ------------------------------------------------------------
def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CalendarService:
    return CalendarService(db)


# ---- Year routes -----------------------------------------------------------

@router.get("/", response_model=ApiResponse[list[CalendarYearSummaryResponse]])
async def list_years(
    service: Annotated[CalendarService, Depends(get_service)],
):
    """List all calendar years with summary statistics."""
    return ApiResponse.ok(await service.get_all_years())


@router.post(
    "/",
    response_model=ApiResponse[CalendarYearDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_year(
    payload: CalendarYearCreate,
    service: Annotated[CalendarService, Depends(get_service)],
):
    """Create a new calendar year with auto-generated days (Mon–Fri: 8h, Sat–Sun: 0h)."""
    return ApiResponse.ok(await service.create_year(payload))


@router.get("/{year}", response_model=ApiResponse[CalendarYearDetailResponse])
async def get_year(
    year: Annotated[int, Path(ge=2000, le=2100)],
    service: Annotated[CalendarService, Depends(get_service)],
):
    """Get full calendar for a year (all 365/366 days)."""
    return ApiResponse.ok(await service.get_year(year))


@router.post(
    "/{year}/approve",
    response_model=ApiResponse[CalendarYearDetailResponse],
)
async def approve_year(
    year: Annotated[int, Path(ge=2000, le=2100)],
    service: Annotated[CalendarService, Depends(get_service)],
):
    """Approve calendar year — after this, days cannot be edited."""
    return ApiResponse.ok(await service.approve_year(year))


# ---- Month routes ----------------------------------------------------------

@router.get(
    "/{year}/{month}",
    response_model=ApiResponse[CalendarMonthResponse],
)
async def get_month(
    year: Annotated[int, Path(ge=2000, le=2100)],
    month: Annotated[int, Path(ge=1, le=12)],
    service: Annotated[CalendarService, Depends(get_service)],
):
    """Get calendar for a specific month with day list and norm."""
    return ApiResponse.ok(await service.get_month(year, month))


@router.get(
    "/{year}/{month}/norm",
    response_model=ApiResponse[MonthNormResponse],
)
async def get_month_norm(
    year: Annotated[int, Path(ge=2000, le=2100)],
    month: Annotated[int, Path(ge=1, le=12)],
    service: Annotated[CalendarService, Depends(get_service)],
):
    """Get working days and hours norm for a month (calculated from calendar data)."""
    return ApiResponse.ok(await service.calculate_month_norm(year, month))


# ---- Day routes ------------------------------------------------------------

@router.patch(
    "/day/{day_id}",
    response_model=ApiResponse[CalendarDayResponse],
)
async def update_day(
    day_id: UUID,
    payload: CalendarDayUpdate,
    service: Annotated[CalendarService, Depends(get_service)],
):
    """Update a single calendar day (type, working hours, comment).

    Cannot be used after year is APPROVED.
    """
    return ApiResponse.ok(await service.update_day(day_id, payload))
