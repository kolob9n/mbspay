"""Payment repository — database access layer."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.payments.models import Payment, PaymentItem, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # Payment
    # ========================================================================

    async def create(
        self,
        *,
        number: str,
        date: date,
        payroll_period_id: UUID,
        comment: str | None = None,
        created_by: UUID | None = None,
    ) -> Payment:
        p = Payment(
            number=number,
            date=date,
            payroll_period_id=payroll_period_id,
            status=PaymentStatus.DRAFT,
            comment=comment,
            created_by=created_by,
        )
        self._session.add(p)
        await self._session.flush()
        return p

    async def get_by_id(
        self, payment_id: UUID, *, with_items: bool = False
    ) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id)
        if with_items:
            stmt = stmt.options(
                joinedload(Payment.items).joinedload(PaymentItem.employee)
            )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_number(self, number: str) -> Payment | None:
        stmt = select(Payment).where(Payment.number == number)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        status: PaymentStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Payment], int]:
        base = select(Payment)
        if status is not None:
            base = base.where(Payment.status == status)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = (
            base.order_by(Payment.date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update(self, payment: Payment, **values) -> Payment:
        for key, val in values.items():
            if val is not None:
                setattr(payment, key, val)
        await self._session.flush()
        return payment

    # ========================================================================
    # PaymentItem
    # ========================================================================

    async def create_items(
        self, payment_id: UUID, items: list[dict]
    ) -> list[PaymentItem]:
        orm_items = [PaymentItem(payment_id=payment_id, **item) for item in items]
        self._session.add_all(orm_items)
        await self._session.flush()
        return orm_items

    async def get_items(self, payment_id: UUID) -> list[PaymentItem]:
        stmt = (
            select(PaymentItem)
            .options(joinedload(PaymentItem.employee))
            .where(PaymentItem.payment_id == payment_id)
            .order_by(PaymentItem.employee_id)
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_total_amount(self, payment_id: UUID) -> Decimal:
        stmt = select(func.coalesce(func.sum(PaymentItem.amount), 0)).where(
            PaymentItem.payment_id == payment_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
