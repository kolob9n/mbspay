"""Defect repository — database access layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.defects.models import Defect, DefectType


class DefectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # DefectType
    # ========================================================================

    async def create_type(self, **values) -> DefectType:
        dt = DefectType(**values)
        self._session.add(dt)
        await self._session.flush()
        return dt

    async def get_type_by_id(self, dt_id: UUID) -> DefectType | None:
        stmt = select(DefectType).where(DefectType.id == dt_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_type_by_code(self, code: str) -> DefectType | None:
        stmt = select(DefectType).where(DefectType.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_types(self) -> list[DefectType]:
        stmt = select(DefectType).order_by(DefectType.code)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_type(self, dt: DefectType, **values) -> DefectType:
        for key, val in values.items():
            if val is not None:
                setattr(dt, key, val)
        await self._session.flush()
        return dt

    # ========================================================================
    # Defect
    # ========================================================================

    async def create(self, **values) -> Defect:
        d = Defect(**values)
        self._session.add(d)
        await self._session.flush()
        return d

    async def get_by_id(self, defect_id: UUID) -> Defect | None:
        stmt = (
            select(Defect)
            .options(joinedload(Defect.employee), joinedload(Defect.defect_type))
            .where(Defect.id == defect_id)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_employee(
        self, employee_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[Defect], int]:
        base = select(Defect).where(Defect.employee_id == employee_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = (
            base.options(joinedload(Defect.defect_type))
            .order_by(Defect.date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(items_stmt)
        return list(result.unique().scalars().all()), total

    async def update(self, defect: Defect, **values) -> Defect:
        for key, val in values.items():
            if val is not None:
                setattr(defect, key, val)
        await self._session.flush()
        return defect

    async def count_by_employee_period(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> int:
        """Count defects for an employee in a payroll period."""
        from app.modules.payroll_periods.repository import PayrollPeriodRepository
        period_repo = PayrollPeriodRepository(self._session)
        period = await period_repo.get_by_id(payroll_period_id)
        if period is None:
            return 0

        import calendar as py_cal
        from datetime import date

        days_in_month = py_cal.monthrange(period.year, period.month)[1]
        start_date = date(period.year, period.month, 1)
        end_date = date(period.year, period.month, days_in_month)

        stmt = select(func.count(Defect.id)).where(
            Defect.employee_id == employee_id,
            Defect.date >= start_date,
            Defect.date <= end_date,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_employee_period_by_type(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> dict[str, int]:
        """Count defects grouped by type code for an employee in a payroll period."""
        from app.modules.payroll_periods.repository import PayrollPeriodRepository
        period_repo = PayrollPeriodRepository(self._session)
        period = await period_repo.get_by_id(payroll_period_id)
        if period is None:
            return {}

        import calendar as py_cal
        from datetime import date

        days_in_month = py_cal.monthrange(period.year, period.month)[1]
        start_date = date(period.year, period.month, 1)
        end_date = date(period.year, period.month, days_in_month)

        stmt = (
            select(DefectType.code, func.count(Defect.id))
            .join(Defect, Defect.defect_type_id == DefectType.id)
            .where(
                Defect.employee_id == employee_id,
                Defect.date >= start_date,
                Defect.date <= end_date,
            )
            .group_by(DefectType.code)
        )
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}
