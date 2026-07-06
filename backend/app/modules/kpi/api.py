"""KPI API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.kpi.schemas import (
    KPIEmployeeResult,
    KPIEmployeeValueCreate,
    KPIEmployeeValueResponse,
    KPIIndicatorCreate,
    KPIIndicatorResponse,
    KPIIndicatorUpdate,
    KPIPeriodCreate,
    KPIPeriodResponse,
    KPIPeriodUpdate,
)
from app.modules.kpi.service import KPIService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/kpi", tags=["KPI"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> KPIService:
    return KPIService(db)


# ---- Indicators ------------------------------------------------------------


@router.get("/indicators", response_model=ApiResponse[list[KPIIndicatorResponse]])
async def list_indicators(
    service: Annotated[KPIService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_indicators(page=page, size=size))


@router.post(
    "/indicators",
    response_model=ApiResponse[KPIIndicatorResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_indicator(
    payload: KPIIndicatorCreate,
    service: Annotated[KPIService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create_indicator(payload))


@router.patch(
    "/indicators/{ind_id}",
    response_model=ApiResponse[KPIIndicatorResponse],
)
async def update_indicator(
    ind_id: UUID,
    payload: KPIIndicatorUpdate,
    service: Annotated[KPIService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update_indicator(ind_id, payload))


# ---- Period values ---------------------------------------------------------


@router.get(
    "/period/{period_id}",
    response_model=ApiResponse[list[KPIPeriodResponse]],
)
async def get_period_values(
    period_id: UUID,
    service: Annotated[KPIService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_period_values(period_id))


@router.post(
    "/period",
    response_model=ApiResponse[KPIPeriodResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_period_value(
    payload: KPIPeriodCreate,
    service: Annotated[KPIService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create_period_value(payload))


@router.patch(
    "/period/{pv_id}",
    response_model=ApiResponse[KPIPeriodResponse],
)
async def update_period_value(
    pv_id: UUID,
    payload: KPIPeriodUpdate,
    service: Annotated[KPIService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update_period_value(pv_id, payload))


# ---- Employee values -------------------------------------------------------


@router.get(
    "/employee/{employee_id}/{period_id}",
    response_model=ApiResponse[KPIEmployeeResult],
)
async def get_employee_kpi(
    employee_id: UUID,
    period_id: UUID,
    service: Annotated[KPIService, Depends(get_service)],
):
    """Calculate and return KPI for an employee in a period."""
    return ApiResponse.ok(
        await service.get_indicator_result(employee_id, period_id)
    )


@router.post(
    "/employee-value",
    response_model=ApiResponse[KPIEmployeeValueResponse],
    status_code=status.HTTP_201_CREATED,
)
async def set_employee_value(
    payload: KPIEmployeeValueCreate,
    service: Annotated[KPIService, Depends(get_service)],
):
    """Manually set an employee KPI value."""
    return ApiResponse.ok(await service.set_employee_value(payload))


# ---- Recalculation ---------------------------------------------------------


@router.post(
    "/recalculate/{period_id}",
    response_model=ApiResponse[list[KPIEmployeeResult]],
)
async def recalculate_period(
    period_id: UUID,
    service: Annotated[KPIService, Depends(get_service)],
):
    """Recalculate KPI for all employees in a period."""
    return ApiResponse.ok(await service.recalculate_period(period_id))
