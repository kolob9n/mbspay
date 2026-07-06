"""Payroll API — HTTP layer."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.payroll.models import PayrollRunStatus
from app.modules.payroll.payslip_service import PayslipService
from app.modules.payroll.schemas import (
    PayrollResultResponse,
    PayrollRunCreate,
    PayrollRunDetailResponse,
    PayrollRunResponse,
    PayslipResponse,
)
from app.modules.payroll.service import PayrollService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/payroll", tags=["Payroll"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PayrollService:
    return PayrollService(db)


def get_payslip_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PayslipService:
    return PayslipService(db)


# ---- PayrollRun CRUD -------------------------------------------------------


@router.get("/", response_model=ApiResponse[list[PayrollRunResponse]])
async def list_runs(
    service: Annotated[PayrollService, Depends(get_service)],
    payroll_period_id: Annotated[Optional[UUID], Query()] = None,
    status_filter: Annotated[Optional[PayrollRunStatus], Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return ApiResponse.ok(
        await service.get_all(
            payroll_period_id=payroll_period_id,
            status=status_filter,
            page=page,
            size=size,
        )
    )


@router.post(
    "/",
    response_model=ApiResponse[PayrollRunResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_run(
    payload: PayrollRunCreate,
    service: Annotated[PayrollService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create_run(payload))


@router.get("/{run_id}", response_model=ApiResponse[PayrollRunDetailResponse])
async def get_run(
    run_id: UUID,
    service: Annotated[PayrollService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_by_id(run_id))


# ---- Calculation -----------------------------------------------------------


@router.post(
    "/{run_id}/calculate",
    response_model=ApiResponse[PayrollRunDetailResponse],
)
async def calculate_run(
    run_id: UUID,
    service: Annotated[PayrollService, Depends(get_service)],
):
    """Run payroll calculation for all employees."""
    return ApiResponse.ok(await service.run_calculation(run_id))


# ---- Workflow --------------------------------------------------------------


@router.post(
    "/{run_id}/approve",
    response_model=ApiResponse[PayrollRunDetailResponse],
)
async def approve_run(
    run_id: UUID,
    service: Annotated[PayrollService, Depends(get_service)],
):
    """Approve payroll → creates ACCRUAL entries in PayrollLedger."""
    return ApiResponse.ok(await service.approve(run_id))


@router.post(
    "/{run_id}/close",
    response_model=ApiResponse[PayrollRunDetailResponse],
)
async def close_run(
    run_id: UUID,
    service: Annotated[PayrollService, Depends(get_service)],
):
    return ApiResponse.ok(await service.close(run_id))


@router.post(
    "/{run_id}/cancel",
    response_model=ApiResponse[PayrollRunDetailResponse],
)
async def cancel_run(
    run_id: UUID,
    service: Annotated[PayrollService, Depends(get_service)],
):
    return ApiResponse.ok(await service.cancel(run_id))


# ---- Results ---------------------------------------------------------------


@router.get("/{run_id}/results", response_model=ApiResponse[list[PayrollResultResponse]])
async def get_results(
    run_id: UUID,
    service: Annotated[PayrollService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_results(run_id))


@router.get("/result/{employee_id}", response_model=ApiResponse[PayrollResultResponse])
async def get_employee_result(
    employee_id: UUID,
    run_id: UUID = Query(...),
    service: Annotated[PayrollService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_employee_result(run_id, employee_id))


# ---- Payslip ---------------------------------------------------------------


@router.get("/payslip/{employee_id}", response_model=ApiResponse[PayslipResponse])
async def get_payslip(
    employee_id: UUID,
    run_id: UUID = Query(...),
    payslip_service: Annotated[PayslipService, Depends(get_payslip_service)],
):
    """Generate employee payslip from calculated payroll results."""
    return ApiResponse.ok(await payslip_service.generate(employee_id, run_id))
