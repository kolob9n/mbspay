"""Ledger service — balance, history, period summary."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payroll_ledger.repository import PayrollLedgerRepository
from app.modules.payroll_ledger.schemas import (
    EmployeeBalanceResponse,
    LedgerEntryResponse,
    PeriodSummaryResponse,
)
from app.shared.exceptions import NotFoundException


class LedgerService:
    """Read-only service for ledger queries. All writes go through PaymentService."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = PayrollLedgerRepository(session)

    async def get_employee_history(
        self,
        employee_id: UUID,
        *,
        payroll_period_id: UUID | None = None,
        page: int = 1,
        size: int = 100,
    ) -> list[LedgerEntryResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_by_employee(
            employee_id,
            payroll_period_id=payroll_period_id,
            offset=offset,
            limit=size,
        )
        return [LedgerEntryResponse.model_validate(e) for e in items]

    async def get_period_entries(
        self, payroll_period_id: UUID
    ) -> list[LedgerEntryResponse]:
        items = await self._repo.get_by_period(payroll_period_id)
        return [LedgerEntryResponse.model_validate(e) for e in items]

    async def calculate_balance(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> EmployeeBalanceResponse:
        accrued, paid, balance = await self._repo.calculate_balance(
            employee_id, payroll_period_id
        )
        return EmployeeBalanceResponse(
            employee_id=employee_id,
            payroll_period_id=payroll_period_id,
            accrued=accrued,
            paid=paid,
            balance=balance,
        )

    async def get_period_summary(
        self, payroll_period_id: UUID
    ) -> PeriodSummaryResponse:
        data = await self._repo.get_period_summary(payroll_period_id)
        return PeriodSummaryResponse(
            payroll_period_id=payroll_period_id,
            **data,
        )
