"""Calendar repository — database access layer.

ALL database operations for calendar live here.
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import (
    CalendarDay,
    CalendarYear,
    DayType,
    YearStatus,
)


class CalendarRepository:
    """Encapsulates all database queries for CalendarYear and CalendarDay."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # CalendarYear
    # ========================================================================

    async def create_year(self, year: int) -> CalendarYear:
        cy = CalendarYear(year=year, status=YearStatus.DRAFT)
        self._session.add(cy)
        await self._session.flush()
        return cy

    async def get_year_by_number(self, year: int) -> CalendarYear | None:
        stmt = select(CalendarYear).where(CalendarYear.year == year)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_year_by_id(self, year_id: UUID) -> CalendarYear | None:
        stmt = select(CalendarYear).where(CalendarYear.id == year_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_years(self) -> list[CalendarYear]:
        stmt = select(CalendarYear).order_by(CalendarYear.year.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def approve_year(self, cy: CalendarYear) -> CalendarYear:
        cy.status = YearStatus.APPROVED
        await self._session.flush()
        return cy

    # ========================================================================
    # CalendarDay — generation
    # ========================================================================

    async def generate_days(
        self, calendar_year_id: UUID, year: int
    ) -> list[CalendarDay]:
        """Generate 365/366 CalendarDay rows for the given year.

        Default rules:
            Mon–Fri → WORKDAY, 8 h
            Sat–Sun → WEEKEND, 0 h
        """
        days: list[CalendarDay] = []
        current = date(year, 1, 1)
        end = date(year, 12, 31)

        while current <= end:
            weekday = current.weekday()  # 0=Mon … 6=Sun
            if weekday < 5:
                day_type = DayType.WORKDAY
                is_working = True
                hours = 8
            else:
                day_type = DayType.WEEKEND
                is_working = False
                hours = 0

            cd = CalendarDay(
                calendar_year_id=calendar_year_id,
                date=current,
                day_type=day_type,
                is_working_day=is_working,
                working_hours=hours,
            )
            self._session.add(cd)
            days.append(cd)
            current += timedelta(days=1)

        await self._session.flush()
        return days

    # ========================================================================
    # CalendarDay — read
    # ========================================================================

    async def get_day(self, day_id: UUID) -> CalendarDay | None:
        stmt = select(CalendarDay).where(CalendarDay.id == day_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_days_by_year(self, calendar_year_id: UUID) -> list[CalendarDay]:
        stmt = (
            select(CalendarDay)
            .where(CalendarDay.calendar_year_id == calendar_year_id)
            .order_by(CalendarDay.date)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_days_by_month(
        self, calendar_year_id: UUID, month: int
    ) -> list[CalendarDay]:
        stmt = (
            select(CalendarDay)
            .where(
                CalendarDay.calendar_year_id == calendar_year_id,
                func.extract("MONTH", CalendarDay.date) == month,
            )
            .order_by(CalendarDay.date)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ========================================================================
    # CalendarDay — update
    # ========================================================================

    async def update_day(self, day: CalendarDay, **values) -> CalendarDay:
        for key, val in values.items():
            if val is not None:
                setattr(day, key, val)
        await self._session.flush()
        return day

    # ========================================================================
    # Norm calculation
    # ========================================================================

    async def calculate_month_norm(
        self, calendar_year_id: UUID, month: int
    ) -> tuple[int, int]:
        """Return (working_days, working_hours) for the given month."""
        stmt = (
            select(
                func.count(CalendarDay.id).filter(CalendarDay.is_working_day == True),
                func.coalesce(
                    func.sum(CalendarDay.working_hours).filter(
                        CalendarDay.is_working_day == True
                    ),
                    0,
                ),
            )
            .where(
                CalendarDay.calendar_year_id == calendar_year_id,
                func.extract("MONTH", CalendarDay.date) == month,
            )
        )
        result = await self._session.execute(stmt)
        row = result.one()
        return int(row[0]), int(row[1])

    # ========================================================================
    # Statistics helpers
    # ========================================================================

    async def get_year_stats(
        self, calendar_year_id: UUID
    ) -> tuple[int, int, int]:
        """Return (total_days, working_days_count, working_hours_total)."""
        stmt = (
            select(
                func.count(CalendarDay.id),
                func.count(CalendarDay.id).filter(CalendarDay.is_working_day == True),
                func.coalesce(
                    func.sum(CalendarDay.working_hours).filter(
                        CalendarDay.is_working_day == True
                    ),
                    0,
                ),
            )
            .where(CalendarDay.calendar_year_id == calendar_year_id)
        )
        result = await self._session.execute(stmt)
        row = result.one()
        return int(row[0]), int(row[1]), int(row[2])
