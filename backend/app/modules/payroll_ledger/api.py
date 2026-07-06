"""PayrollLedger API — HTTP layer (read-only)."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.payroll_ledger.schemas import (
    EmployeeBalanceResponse,
    LedgerEntryResponse,
    PeriodSummaryResponse,
)
from app.modules.payroll_ledger.service import LedgerService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/ledger", tags=["Payroll Ledger"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> LedgerService:
    return LedgerService(db)


@router.get("/", response_model=ApiResponse[list[LedgerEntryResponse]])
async def get_period_ledger(
    payroll_period_id: UUID = Query(...),
    service: Annotated[LedgerService, Depends(get_service)],
):
    """Get all ledger entries for a period."""
    return ApiResponse.ok(await service.get_period_entries(payroll_period_id))


@router.get(
    "/employee/{employee_id}",
    response_model=ApiResponse[list[LedgerEntryResponse]],
)
async def get_employee_history(
    employee_id: UUID,
    payroll_period_id: Annotated[Optional[UUID], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
    service: Annotated[LedgerService, Depends(get_service)],
):
    """Get ledger history for an employee (optionally filtered by period)."""
    return ApiResponse.ok(
        await service.get_employee_history(
            employee_id, payroll_period_id=payroll_period_id, page=page, size=size
        )
    )


@router.get(
    "/period/{period_id}",
    response_model=ApiResponse[PeriodSummaryResponse],
)
async def get_period_summary(
    period_id: UUID,
    service: Annotated[LedgerService, Depends(get_service)],
):
    """Get aggregated period summary."""
    return ApiResponse.ok(await service.get_period_summary(period_id))


@router.get(
    "/balance/{employee_id}/{period_id}",
    response_model=ApiResponse[EmployeeBalanceResponse],
)
async def get_balance(
    employee_id: UUID,
    period_id: UUID,
    service: Annotated[LedgerService, Depends(get_service)],
):
    """Calculate balance for employee+period from ledger entries.

    Returns: {accrued, paid, balance}
    """
    return ApiResponse.ok(await service.calculate_balance(employee_id, period_id))
