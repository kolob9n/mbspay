"""KPI repository — database access layer."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.kpi.models import (
    KPIIndicator,
    KPIEmployeeValue,
    KPIPeriod,
    KPISource,
)


class KPIRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # KPIIndicator
    # ========================================================================

    async def create_indicator(self, **values) -> KPIIndicator:
        ind = KPIIndicator(**values)
        self._session.add(ind)
        await self._session.flush()
        return ind

    async def get_indicator_by_id(self, ind_id: UUID) -> KPIIndicator | None:
        stmt = select(KPIIndicator).where(KPIIndicator.id == ind_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_indicator_by_code(self, code: str) -> KPIIndicator | None:
        stmt = select(KPIIndicator).where(KPIIndicator.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_indicators(
        self, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[KPIIndicator], int]:
        base = select(KPIIndicator)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(KPIIndicator.code).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def get_active_indicators(self) -> list[KPIIndicator]:
        stmt = select(KPIIndicator).where(
            KPIIndicator.is_active == True  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_indicator(self, ind: KPIIndicator, **values) -> KPIIndicator:
        for key, val in values.items():
            if val is not None:
                setattr(ind, key, val)
        await self._session.flush()
        return ind

    # ========================================================================
    # KPIPeriod
    # ========================================================================

    async def create_period_value(self, **values) -> KPIPeriod:
        pv = KPIPeriod(**values)
        self._session.add(pv)
        await self._session.flush()
        return pv

    async def get_period_values(
        self, payroll_period_id: UUID
    ) -> list[KPIPeriod]:
        stmt = (
            select(KPIPeriod)
            .options(joinedload(KPIPeriod.indicator))
            .where(KPIPeriod.payroll_period_id == payroll_period_id)
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_period_value_by_id(self, pv_id: UUID) -> KPIPeriod | None:
        stmt = select(KPIPeriod).where(KPIPeriod.id == pv_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_period_value(self, pv: KPIPeriod, **values) -> KPIPeriod:
        for key, val in values.items():
            if val is not None:
                setattr(pv, key, val)
        await self._session.flush()
        return pv

    # ========================================================================
    # KPIEmployeeValue
    # ========================================================================

    async def create_employee_value(self, **values) -> KPIEmployeeValue:
        ev = KPIEmployeeValue(**values)
        self._session.add(ev)
        await self._session.flush()
        return ev

    async def get_employee_values(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> list[KPIEmployeeValue]:
        stmt = (
            select(KPIEmployeeValue)
            .options(
                joinedload(KPIEmployeeValue.indicator),
                joinedload(KPIEmployeeValue.employee),
            )
            .where(
                KPIEmployeeValue.employee_id == employee_id,
                KPIEmployeeValue.payroll_period_id == payroll_period_id,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def upsert_employee_value(
        self,
        employee_id: UUID,
        payroll_period_id: UUID,
        indicator_id: UUID,
        value: Decimal,
        source: KPISource = KPISource.SYSTEM,
    ) -> KPIEmployeeValue:
        """Update existing or create new employee KPI value."""
        stmt = select(KPIEmployeeValue).where(
            KPIEmployeeValue.employee_id == employee_id,
            KPIEmployeeValue.payroll_period_id == payroll_period_id,
            KPIEmployeeValue.indicator_id == indicator_id,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.value = value
            existing.source = source
            await self._session.flush()
            return existing

        ev = KPIEmployeeValue(
            employee_id=employee_id,
            payroll_period_id=payroll_period_id,
            indicator_id=indicator_id,
            value=value,
            source=source,
        )
        self._session.add(ev)
        await self._session.flush()
        return ev

    async def get_all_employee_values(
        self, payroll_period_id: UUID
    ) -> list[KPIEmployeeValue]:
        stmt = (
            select(KPIEmployeeValue)
            .options(
                joinedload(KPIEmployeeValue.indicator),
                joinedload(KPIEmployeeValue.employee),
            )
            .where(KPIEmployeeValue.payroll_period_id == payroll_period_id)
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())
