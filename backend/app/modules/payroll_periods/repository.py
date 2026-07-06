"""PayrollPeriod repository — database access layer."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_

from app.modules.payroll_periods.models import PayrollPeriod, PeriodStatus


class PayrollPeriodRepository:
    """Encapsulates all database operations for PayrollPeriod.

    This is the ONLY place where SQLAlchemy queries live.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- Create ------------------------------------------------------------

    async def create(self, *, year: int, month: int, created_by: UUID | None = None) -> PayrollPeriod:
        period = PayrollPeriod(
            year=year,
            month=month,
            status=PeriodStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        self._session.add(period)
        await self._session.flush()
        return period

    # ---- Read --------------------------------------------------------------

    async def get_by_id(self, period_id: UUID) -> PayrollPeriod | None:
        stmt = select(PayrollPeriod).where(
            PayrollPeriod.id == period_id,
            PayrollPeriod.is_deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_year_month(self, year: int, month: int) -> PayrollPeriod | None:
        stmt = select(PayrollPeriod).where(
            PayrollPeriod.year == year,
            PayrollPeriod.month == month,
            PayrollPeriod.is_deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_current(self) -> PayrollPeriod | None:
        """Return the latest non-closed period (by year, month desc)."""
        stmt = (
            select(PayrollPeriod)
            .where(
                PayrollPeriod.status != PeriodStatus.CLOSED,
                PayrollPeriod.is_deleted == False,  # noqa: E712
            )
            .order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_previous_period(self, year: int, month: int) -> PayrollPeriod | None:
        """Return the period immediately before the given year/month."""
        stmt = (
            select(PayrollPeriod)
            .where(
                and_(
                    PayrollPeriod.is_deleted == False,  # noqa: E712
                    (
                        (PayrollPeriod.year == year) & (PayrollPeriod.month < month)
                    )
                    | (PayrollPeriod.year < year),
                )
            )
            .order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        status: PeriodStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[PayrollPeriod], int]:
        """Return a paginated list of periods, ordered by year/month desc."""

        base = select(PayrollPeriod).where(PayrollPeriod.is_deleted == False)  # noqa: E712

        if status is not None:
            base = base.where(PayrollPeriod.status == status)

        # Count
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        # Items
        items_stmt = base.order_by(
            PayrollPeriod.year.desc(), PayrollPeriod.month.desc()
        ).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # ---- Update ------------------------------------------------------------

    async def update(self, period: PayrollPeriod, **values) -> PayrollPeriod:
        for key, val in values.items():
            setattr(period, key, val)
        await self._session.flush()
        return period

    # ---- Close -------------------------------------------------------------

    async def close(self, period: PayrollPeriod) -> PayrollPeriod:
        period.status = PeriodStatus.CLOSED
        period.closed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return period
