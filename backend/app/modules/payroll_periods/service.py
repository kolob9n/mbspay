"""PayrollPeriod service — business logic layer."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payroll_periods.models import PeriodStatus
from app.modules.payroll_periods.repository import PayrollPeriodRepository
from app.modules.payroll_periods.schemas import (
    PayrollPeriodCreate,
    PayrollPeriodListResponse,
    PayrollPeriodResponse,
    PayrollPeriodUpdate,
)
from app.shared.exceptions import BusinessRuleException, ConflictException, NotFoundException


class PayrollPeriodService:
    """All business rules for payroll periods live here.

    This layer NEVER touches SQLAlchemy directly — only calls Repository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = PayrollPeriodRepository(session)

    # ---- Create ------------------------------------------------------------

    async def create_period(
        self, payload: PayrollPeriodCreate, *, created_by: UUID | None = None
    ) -> PayrollPeriodResponse:
        """Create a new payroll period, enforcing business rules."""

        # Rule 1: no duplicate year/month
        existing = await self._repo.get_by_year_month(payload.year, payload.month)
        if existing is not None:
            raise ConflictException(
                f"Период {payload.year}-{payload.month:02d} уже существует."
            )

        # Rule 2: cannot create next month if previous is still open
        previous = await self._repo.get_previous_period(payload.year, payload.month)
        if previous is not None and previous.status != PeriodStatus.CLOSED:
            raise BusinessRuleException(
                f"Нельзя создать период {payload.year}-{payload.month:02d}: "
                f"предыдущий период {previous.period_label} ещё не закрыт "
                f"(статус: {previous.status.value})."
            )

        period = await self._repo.create(
            year=payload.year,
            month=payload.month,
            created_by=created_by,
        )
        return PayrollPeriodResponse.model_validate(period)

    # ---- Read --------------------------------------------------------------

    async def get_period(self, period_id: UUID) -> PayrollPeriodResponse:
        period = await self._repo.get_by_id(period_id)
        if period is None:
            raise NotFoundException(f"Период с id={period_id} не найден.")
        return PayrollPeriodResponse.model_validate(period)

    async def get_current_period(self) -> PayrollPeriodResponse | None:
        period = await self._repo.get_current()
        if period is None:
            return None
        return PayrollPeriodResponse.model_validate(period)

    async def get_periods(
        self,
        *,
        status: PeriodStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PayrollPeriodListResponse:
        offset = (page - 1) * size
        items, total = await self._repo.get_all(
            status=status, offset=offset, limit=size
        )
        return PayrollPeriodListResponse(
            items=[PayrollPeriodResponse.model_validate(p) for p in items],
            total=total,
        )

    # ---- Update ------------------------------------------------------------

    async def update_period(
        self, period_id: UUID, payload: PayrollPeriodUpdate
    ) -> PayrollPeriodResponse:
        period = await self._repo.get_by_id(period_id)
        if period is None:
            raise NotFoundException(f"Период с id={period_id} не найден.")

        # Rule 3: cannot modify a closed period
        if period.status == PeriodStatus.CLOSED:
            raise BusinessRuleException(
                f"Нельзя изменить закрытый период {period.period_label}."
            )

        updated = await self._repo.update(period, status=payload.status)
        return PayrollPeriodResponse.model_validate(updated)

    # ---- Close -------------------------------------------------------------

    async def close_period(self, period_id: UUID) -> PayrollPeriodResponse:
        period = await self._repo.get_by_id(period_id)
        if period is None:
            raise NotFoundException(f"Период с id={period_id} не найден.")

        if period.status == PeriodStatus.CLOSED:
            raise BusinessRuleException(
                f"Период {period.period_label} уже закрыт."
            )

        closed = await self._repo.close(period)
        return PayrollPeriodResponse.model_validate(closed)
