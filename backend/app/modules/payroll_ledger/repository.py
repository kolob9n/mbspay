"""PayrollLedger repository — database access layer.

All CRUD for the immutable ledger registry.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payroll_ledger.models import (
    DocumentType,
    OperationType,
    PayrollLedgerEntry,
)


class PayrollLedgerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # Create entry
    # ========================================================================

    async def create_entry(
        self,
        *,
        employee_id: UUID,
        payroll_period_id: UUID,
        document_type: DocumentType,
        document_id: UUID,
        operation_type: OperationType,
        amount: Decimal,
        operation_date: datetime,
    ) -> PayrollLedgerEntry:
        entry = PayrollLedgerEntry(
            employee_id=employee_id,
            payroll_period_id=payroll_period_id,
            document_type=document_type,
            document_id=document_id,
            operation_type=operation_type,
            amount=amount,
            operation_date=operation_date,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    # ========================================================================
    # Read
    # ========================================================================

    async def get_by_id(self, entry_id: UUID) -> PayrollLedgerEntry | None:
        stmt = select(PayrollLedgerEntry).where(PayrollLedgerEntry.id == entry_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_employee(
        self,
        employee_id: UUID,
        *,
        payroll_period_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[PayrollLedgerEntry], int]:
        base = select(PayrollLedgerEntry).where(
            PayrollLedgerEntry.employee_id == employee_id
        )
        if payroll_period_id is not None:
            base = base.where(
                PayrollLedgerEntry.payroll_period_id == payroll_period_id
            )

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        items_stmt = (
            base.order_by(PayrollLedgerEntry.operation_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def get_by_period(
        self, payroll_period_id: UUID
    ) -> list[PayrollLedgerEntry]:
        stmt = (
            select(PayrollLedgerEntry)
            .where(PayrollLedgerEntry.payroll_period_id == payroll_period_id)
            .order_by(PayrollLedgerEntry.employee_id, PayrollLedgerEntry.operation_date)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ========================================================================
    # Balance calculation
    # ========================================================================

    async def calculate_balance(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Return (accrued, paid, balance) for employee+period.

        accrued = Σ(ACCRUAL amounts)
        paid    = Σ(PAYMENT amounts)   ← payments are positive in ledger
        balance = accrued - paid + Σ(CORRECTION amounts)
        """
        stmt = (
            select(
                func.coalesce(
                    func.sum(PayrollLedgerEntry.amount).filter(
                        PayrollLedgerEntry.operation_type == OperationType.ACCRUAL
                    ),
                    0,
                ).label("accrued"),
                func.coalesce(
                    func.sum(PayrollLedgerEntry.amount).filter(
                        PayrollLedgerEntry.operation_type == OperationType.PAYMENT
                    ),
                    0,
                ).label("paid"),
                func.coalesce(
                    func.sum(PayrollLedgerEntry.amount).filter(
                        PayrollLedgerEntry.operation_type == OperationType.CORRECTION
                    ),
                    0,
                ).label("correction"),
            )
            .where(
                PayrollLedgerEntry.employee_id == employee_id,
                PayrollLedgerEntry.payroll_period_id == payroll_period_id,
            )
        )
        result = await self._session.execute(stmt)
        row = result.one()
        accrued = Decimal(row[0])
        paid = Decimal(row[1])
        correction = Decimal(row[2])
        balance = accrued - paid + correction
        return accrued, paid, balance

    async def get_period_summary(
        self, payroll_period_id: UUID
    ) -> dict:
        """Aggregated summary for the period."""
        entries = await self.get_by_period(payroll_period_id)
        employee_ids = set(e.employee_id for e in entries)

        total_accrued = sum(
            e.amount for e in entries if e.operation_type == OperationType.ACCRUAL
        )
        total_paid = sum(
            e.amount for e in entries if e.operation_type == OperationType.PAYMENT
        )
        total_correction = sum(
            e.amount for e in entries if e.operation_type == OperationType.CORRECTION
        )

        return {
            "total_accrued": Decimal(str(total_accrued)),
            "total_paid": Decimal(str(total_paid)),
            "total_balance": Decimal(str(total_accrued - total_paid + total_correction)),
            "employee_count": len(employee_ids),
        }
