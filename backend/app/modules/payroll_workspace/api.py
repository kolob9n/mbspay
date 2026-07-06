"""Payroll Workspace API — accountant's single-screen workflow."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.payroll_workspace.schemas import (
    ActionResponse,
    KPIStatusResponse,
    PaymentStatusResponse,
    PayrollStatusResponse,
    WorkspaceError,
    WorkspaceStatusResponse,
)
from app.modules.payroll_workspace.service import PayrollWorkspaceService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/payroll-workspace", tags=["Payroll Workspace"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PayrollWorkspaceService:
    return PayrollWorkspaceService(db)


@router.get("/status/{period_id}", response_model=ApiResponse[WorkspaceStatusResponse])
async def get_status(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_period_status(period_id))


@router.get("/kpi-status/{period_id}", response_model=ApiResponse[KPIStatusResponse])
async def get_kpi_status(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_kpi_status(period_id))


@router.get("/payment-status/{period_id}", response_model=ApiResponse[PaymentStatusResponse])
async def get_payment_status(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_payment_status(period_id))


@router.get("/payroll-status/{period_id}", response_model=ApiResponse[PayrollStatusResponse])
async def get_payroll_status(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_payroll_status(period_id))


@router.get("/errors/{period_id}", response_model=ApiResponse[list[WorkspaceError]])
async def get_errors(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_errors(period_id))


@router.post("/calculate-kpi/{period_id}", response_model=ApiResponse[ActionResponse])
async def calculate_kpi(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.calculate_kpi(period_id))


@router.post("/calculate-payroll/{period_id}", response_model=ApiResponse[ActionResponse])
async def calculate_payroll(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.calculate_payroll(period_id))


@router.post("/approve-payroll/{period_id}", response_model=ApiResponse[ActionResponse])
async def approve_payroll(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.approve_payroll(period_id))


@router.post("/close-period/{period_id}", response_model=ApiResponse[ActionResponse])
async def close_period(
    period_id: UUID,
    service: Annotated[PayrollWorkspaceService, Depends(get_service)],
):
    return ApiResponse.ok(await service.close_period(period_id))
