"""Payroll repository — database access layer."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.payroll.models import (
    PayrollResult,
    PayrollRun,
    PayrollRunStatus,
)


class PayrollRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # PayrollRun
    # ========================================================================

    async def create_run(
        self,
        *,
        number: str,
        payroll_period_id: UUID,
        version: int = 1,
        created_by: UUID | None = None,
    ) -> PayrollRun:
        run = PayrollRun(
            number=number,
            payroll_period_id=payroll_period_id,
            status=PayrollRunStatus.DRAFT,
            version=version,
            created_by=created_by,
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_by_id(
        self, run_id: UUID, *, with_results: bool = False
    ) -> PayrollRun | None:
        stmt = select(PayrollRun).where(PayrollRun.id == run_id)
        if with_results:
            stmt = stmt.options(joinedload(PayrollRun.results).joinedload(PayrollResult.employee))
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_last_version(
        self, payroll_period_id: UUID
    ) -> PayrollRun | None:
        stmt = (
            select(PayrollRun)
            .where(PayrollRun.payroll_period_id == payroll_period_id)
            .order_by(PayrollRun.version.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        payroll_period_id: UUID | None = None,
        status: PayrollRunStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[PayrollRun], int]:
        base = select(PayrollRun)
        if payroll_period_id is not None:
            base = base.where(PayrollRun.payroll_period_id == payroll_period_id)
        if status is not None:
            base = base.where(PayrollRun.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        items_stmt = (
            base.order_by(PayrollRun.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update_run(self, run: PayrollRun, **values) -> PayrollRun:
        for key, val in values.items():
            if val is not None:
                setattr(run, key, val)
        await self._session.flush()
        return run

    async def approve(self, run: PayrollRun) -> PayrollRun:
        run.status = PayrollRunStatus.APPROVED
        run.approved_at = datetime.now(timezone.utc)
        await self._session.flush()
        return run

    async def close(self, run: PayrollRun) -> PayrollRun:
        run.status = PayrollRunStatus.CLOSED
        await self._session.flush()
        return run

    async def cancel(self, run: PayrollRun) -> PayrollRun:
        run.status = PayrollRunStatus.CANCELLED
        await self._session.flush()
        return run

    # ========================================================================
    # PayrollResult
    # ========================================================================

    async def create_result(self, **values) -> PayrollResult:
        pr = PayrollResult(**values)
        self._session.add(pr)
        await self._session.flush()
        return pr

    async def clear_results(self, run_id: UUID) -> None:
        """Delete all results for a run (used when recalculating same version)."""
        stmt = select(PayrollResult).where(PayrollResult.payroll_run_id == run_id)
        result = await self._session.execute(stmt)
        for r in result.scalars().all():
            await self._session.delete(r)
        await self._session.flush()

    async def get_results(self, run_id: UUID) -> list[PayrollResult]:
        stmt = (
            select(PayrollResult)
            .options(joinedload(PayrollResult.employee))
            .where(PayrollResult.payroll_run_id == run_id)
            .order_by(PayrollResult.employee_id)
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_employee_result(
        self, run_id: UUID, employee_id: UUID
    ) -> PayrollResult | None:
        stmt = (
            select(PayrollResult)
            .options(joinedload(PayrollResult.employee))
            .where(
                PayrollResult.payroll_run_id == run_id,
                PayrollResult.employee_id == employee_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_results_by_employee(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> list[PayrollResult]:
        stmt = (
            select(PayrollResult)
            .options(joinedload(PayrollResult.employee))
            .where(
                PayrollResult.employee_id == employee_id,
                PayrollResult.payroll_run.has(
                    payroll_period_id=payroll_period_id
                ),
            )
            .order_by(PayrollResult.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def has_accrued(self, run_id: UUID) -> bool:
        """Check if this run has already been accrued in the ledger."""
        from app.modules.payroll_ledger.models import (
            DocumentType,
            PayrollLedgerEntry,
            OperationType,
        )

        stmt = select(func.count(PayrollLedgerEntry.id)).where(
            PayrollLedgerEntry.document_type == DocumentType.PAYROLL,
            PayrollLedgerEntry.document_id == run_id,
            PayrollLedgerEntry.operation_type == OperationType.ACCRUAL,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
