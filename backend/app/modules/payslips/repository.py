"""Payslip repository — database access layer."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.payslips.models import Payslip, PayslipItem, PayslipStatus


class PayslipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **values) -> Payslip:
        ps = Payslip(**values)
        self._session.add(ps)
        await self._session.flush()
        return ps

    async def create_items(self, payslip_id: UUID, items: list[dict]) -> list[PayslipItem]:
        orm_items = [PayslipItem(payslip_id=payslip_id, **i) for i in items]
        self._session.add_all(orm_items)
        await self._session.flush()
        return orm_items

    async def get_by_id(self, ps_id: UUID) -> Payslip | None:
        stmt = (
            select(Payslip)
            .options(joinedload(Payslip.items), joinedload(Payslip.employee), joinedload(Payslip.payroll_run))
            .where(Payslip.id == ps_id)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_employee(
        self, employee_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[Payslip], int]:
        base = select(Payslip).where(Payslip.employee_id == employee_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(Payslip.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def get_all(
        self,
        *,
        payroll_period_id: UUID | None = None,
        employee_id: UUID | None = None,
        status: PayslipStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Payslip], int]:
        base = select(Payslip)
        if payroll_period_id: base = base.where(Payslip.payroll_period_id == payroll_period_id)
        if employee_id: base = base.where(Payslip.employee_id == employee_id)
        if status: base = base.where(Payslip.status == status)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(Payslip.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update(self, payslip: Payslip, **values) -> Payslip:
        for k, v in values.items():
            if v is not None: setattr(payslip, k, v)
        await self._session.flush()
        return payslip
