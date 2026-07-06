"""Calendar service — all business logic for production calendar."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarDay, CalendarYear, YearStatus
from app.modules.calendar.repository import CalendarRepository
from app.modules.calendar.schemas import (
    CalendarDayResponse,
    CalendarDayUpdate,
    CalendarMonthResponse,
    CalendarYearCreate,
    CalendarYearDetailResponse,
    CalendarYearSummaryResponse,
    MonthNormResponse,
)
from app.shared.exceptions import BusinessRuleException, ConflictException, NotFoundException


class CalendarService:
    """Production calendar domain logic.

    No SQLAlchemy here — only Repository calls and business rules.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CalendarRepository(session)

    # ========================================================================
    # Create year + auto-generate days
    # ========================================================================

    async def create_year(
        self, payload: CalendarYearCreate
    ) -> CalendarYearDetailResponse:
        """Create a new calendar year and auto-generate all 365/366 days."""

        # Rule: year must not already exist
        existing = await self._repo.get_year_by_number(payload.year)
        if existing is not None:
            raise ConflictException(
                f"Календарь на {payload.year} год уже существует."
            )

        cy = await self._repo.create_year(payload.year)
        await self._repo.generate_days(cy.id, payload.year)

        return await self._get_year_detail(cy)

    # ========================================================================
    # Read – years
    # ========================================================================

    async def get_all_years(self) -> list[CalendarYearSummaryResponse]:
        years = await self._repo.get_all_years()
        result: list[CalendarYearSummaryResponse] = []
        for cy in years:
            total, wd, wh = await self._repo.get_year_stats(cy.id)
            result.append(
                CalendarYearSummaryResponse(
                    id=cy.id,
                    year=cy.year,
                    status=cy.status,
                    total_days=total,
                    working_days_count=wd,
                    working_hours_total=wh,
                    created_at=cy.created_at,
                    updated_at=cy.updated_at,
                )
            )
        return result

    async def get_year(self, year: int) -> CalendarYearDetailResponse:
        cy = await self._repo.get_year_by_number(year)
        if cy is None:
            raise NotFoundException(f"Календарь на {year} год не найден.")
        return await self._get_year_detail(cy)

    async def get_year_by_id(self, year_id: UUID) -> CalendarYearDetailResponse:
        cy = await self._repo.get_year_by_id(year_id)
        if cy is None:
            raise NotFoundException(f"Календарь с id={year_id} не найден.")
        return await self._get_year_detail(cy)

    # ========================================================================
    # Read – months
    # ========================================================================

    async def get_month(self, year: int, month: int) -> CalendarMonthResponse:
        if month < 1 or month > 12:
            raise BusinessRuleException("Месяц должен быть от 1 до 12.")

        cy = await self._repo.get_year_by_number(year)
        if cy is None:
            raise NotFoundException(f"Календарь на {year} год не найден.")

        days = await self._repo.get_days_by_month(cy.id, month)
        working_days, working_hours = await self._repo.calculate_month_norm(
            cy.id, month
        )

        return CalendarMonthResponse(
            year=year,
            month=month,
            status=cy.status,
            days=[CalendarDayResponse.model_validate(d) for d in days],
            norm=MonthNormResponse(
                year=year,
                month=month,
                working_days=working_days,
                working_hours=working_hours,
            ),
        )

    # ========================================================================
    # Norm calculation
    # ========================================================================

    async def calculate_month_norm(
        self, year: int, month: int
    ) -> MonthNormResponse:
        if month < 1 or month > 12:
            raise BusinessRuleException("Месяц должен быть от 1 до 12.")

        cy = await self._repo.get_year_by_number(year)
        if cy is None:
            raise NotFoundException(f"Календарь на {year} год не найден.")

        working_days, working_hours = await self._repo.calculate_month_norm(
            cy.id, month
        )
        return MonthNormResponse(
            year=year,
            month=month,
            working_days=working_days,
            working_hours=working_hours,
        )

    # ========================================================================
    # Update day
    # ========================================================================

    async def update_day(
        self, day_id: UUID, payload: CalendarDayUpdate
    ) -> CalendarDayResponse:
        day = await self._repo.get_day(day_id)
        if day is None:
            raise NotFoundException(f"Календарный день с id={day_id} не найден.")

        # Load parent year to check status
        cy = await self._repo.get_year_by_id(day.calendar_year_id)
        if cy is None:
            raise NotFoundException("Календарный год не найден.")

        # Rule: cannot edit an APPROVED year
        if cy.status == YearStatus.APPROVED:
            raise BusinessRuleException(
                f"Нельзя редактировать день: календарь {cy.year} года утверждён."
            )

        updated = await self._repo.update_day(
            day,
            day_type=payload.day_type,
            is_working_day=payload.is_working_day,
            working_hours=payload.working_hours,
            comment=payload.comment,
        )
        return CalendarDayResponse.model_validate(updated)

    # ========================================================================
    # Approve year
    # ========================================================================

    async def approve_year(self, year: int) -> CalendarYearDetailResponse:
        cy = await self._repo.get_year_by_number(year)
        if cy is None:
            raise NotFoundException(f"Календарь на {year} год не найден.")

        if cy.status == YearStatus.APPROVED:
            raise BusinessRuleException(
                f"Календарь на {year} год уже утверждён."
            )

        await self._repo.approve_year(cy)
        return await self._get_year_detail(cy)

    # ========================================================================
    # Helpers
    # ========================================================================

    async def _get_year_detail(self, cy: CalendarYear) -> CalendarYearDetailResponse:
        total, wd, wh = await self._repo.get_year_stats(cy.id)
        days = await self._repo.get_days_by_year(cy.id)
        return CalendarYearDetailResponse(
            id=cy.id,
            year=cy.year,
            status=cy.status,
            total_days=total,
            working_days_count=wd,
            working_hours_total=wh,
            created_at=cy.created_at,
            updated_at=cy.updated_at,
            days=[CalendarDayResponse.model_validate(d) for d in days],
        )
