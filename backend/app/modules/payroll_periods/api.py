"""PayrollPeriod API — HTTP layer.

Thin layer: receives request → calls Service → wraps in ApiResponse.
No business logic, no SQLAlchemy.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.payroll_periods.models import PeriodStatus
from app.modules.payroll_periods.schemas import (
    PayrollPeriodCreate,
    PayrollPeriodListResponse,
    PayrollPeriodResponse,
    PayrollPeriodUpdate,
)
from app.modules.payroll_periods.service import PayrollPeriodService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/periods", tags=["Payroll Periods"])


# ---- Dependency ------------------------------------------------------------
def get_period_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PayrollPeriodService:
    return PayrollPeriodService(db)


# ---- Routes ----------------------------------------------------------------

@router.get("/", response_model=ApiResponse[PayrollPeriodListResponse])
async def list_periods(
    service: Annotated[PayrollPeriodService, Depends(get_period_service)],
    status_filter: Annotated[Optional[PeriodStatus], Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List all payroll periods with optional status filter."""
    return ApiResponse.ok(
        await service.get_periods(status=status_filter, page=page, size=size)
    )


@router.get("/current", response_model=ApiResponse[Optional[PayrollPeriodResponse]])
async def get_current_period(
    service: Annotated[PayrollPeriodService, Depends(get_period_service)],
):
    """Return the current (latest non-closed) period, or null."""
    return ApiResponse.ok(await service.get_current_period())


@router.get("/{period_id}", response_model=ApiResponse[PayrollPeriodResponse])
async def get_period(
    period_id: UUID,
    service: Annotated[PayrollPeriodService, Depends(get_period_service)],
):
    """Get a single payroll period by ID."""
    return ApiResponse.ok(await service.get_period(period_id))


@router.post(
    "/",
    response_model=ApiResponse[PayrollPeriodResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_period(
    payload: PayrollPeriodCreate,
    service: Annotated[PayrollPeriodService, Depends(get_period_service)],
):
    """Create a new payroll period."""
    return ApiResponse.ok(await service.create_period(payload))


@router.patch("/{period_id}", response_model=ApiResponse[PayrollPeriodResponse])
async def update_period(
    period_id: UUID,
    payload: PayrollPeriodUpdate,
    service: Annotated[PayrollPeriodService, Depends(get_period_service)],
):
    """Update a payroll period (status only)."""
    return ApiResponse.ok(await service.update_period(period_id, payload))


@router.post("/{period_id}/close", response_model=ApiResponse[PayrollPeriodResponse])
async def close_period(
    period_id: UUID,
    service: Annotated[PayrollPeriodService, Depends(get_period_service)],
):
    """Close a payroll period."""
    return ApiResponse.ok(await service.close_period(period_id))
