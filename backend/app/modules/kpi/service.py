"""KPI service — business logic for KPI calculation."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.repository import EmployeeRepository
from app.modules.formula_engine.repository import FormulaRepository
from app.modules.kpi.models import KPISource
from app.modules.kpi.repository import KPIRepository
from app.modules.kpi.schemas import (
    KPIEmployeeResult,
    KPIEmployeeValueCreate,
    KPIEmployeeValueResponse,
    KPIIndicatorCreate,
    KPIIndicatorResponse,
    KPIIndicatorUpdate,
    KPIPeriodCreate,
    KPIPeriodResponse,
    KPIPeriodUpdate,
)
from app.shared.exceptions import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
)
from app.shared.formula_engine import FormulaEngine, FormulaError


class KPIService:
    """KPI domain logic — indicator management + calculation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = KPIRepository(session)
        self._formula_repo = FormulaRepository(session)
        self._emp_repo = EmployeeRepository(session)
        self._engine = FormulaEngine()

    # ========================================================================
    # KPIIndicator CRUD
    # ========================================================================

    async def create_indicator(
        self, payload: KPIIndicatorCreate
    ) -> KPIIndicatorResponse:
        existing = await self._repo.get_indicator_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Показатель с кодом '{payload.code}' уже существует.")

        formula = await self._formula_repo.get_by_id(payload.formula_id)
        if formula is None:
            raise NotFoundException(f"Формула с id={payload.formula_id} не найдена.")

        ind = await self._repo.create_indicator(**payload.model_dump())
        return KPIIndicatorResponse.model_validate(ind)

    async def get_indicators(
        self, *, page: int = 1, size: int = 100
    ) -> list[KPIIndicatorResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all_indicators(offset=offset, limit=size)
        return [KPIIndicatorResponse.model_validate(i) for i in items]

    async def update_indicator(
        self, ind_id: UUID, payload: KPIIndicatorUpdate
    ) -> KPIIndicatorResponse:
        ind = await self._repo.get_indicator_by_id(ind_id)
        if ind is None:
            raise NotFoundException(f"Показатель с id={ind_id} не найден.")

        if payload.formula_id is not None:
            formula = await self._formula_repo.get_by_id(payload.formula_id)
            if formula is None:
                raise NotFoundException(f"Формула с id={payload.formula_id} не найдена.")

        updated = await self._repo.update_indicator(
            ind, **payload.model_dump(exclude_none=True)
        )
        return KPIIndicatorResponse.model_validate(updated)

    # ========================================================================
    # KPIPeriod CRUD
    # ========================================================================

    async def create_period_value(
        self, payload: KPIPeriodCreate, *, created_by: UUID | None = None
    ) -> KPIPeriodResponse:
        ind = await self._repo.get_indicator_by_id(payload.indicator_id)
        if ind is None:
            raise NotFoundException(f"Показатель с id={payload.indicator_id} не найден.")
        pv = await self._repo.create_period_value(
            payroll_period_id=payload.payroll_period_id,
            indicator_id=payload.indicator_id,
            value=payload.value,
            comment=payload.comment,
            created_by=created_by,
        )
        return KPIPeriodResponse.model_validate(pv)

    async def get_period_values(
        self, period_id: UUID
    ) -> list[KPIPeriodResponse]:
        items = await self._repo.get_period_values(period_id)
        return [KPIPeriodResponse.model_validate(p) for p in items]

    async def update_period_value(
        self, pv_id: UUID, payload: KPIPeriodUpdate
    ) -> KPIPeriodResponse:
        pv = await self._repo.get_period_value_by_id(pv_id)
        if pv is None:
            raise NotFoundException(f"Значение периода с id={pv_id} не найдено.")
        updated = await self._repo.update_period_value(
            pv, **payload.model_dump(exclude_none=True)
        )
        return KPIPeriodResponse.model_validate(updated)

    # ========================================================================
    # KPIEmployeeValue
    # ========================================================================

    async def set_employee_value(
        self, payload: KPIEmployeeValueCreate
    ) -> KPIEmployeeValueResponse:
        emp = await self._emp_repo.get_by_id(payload.employee_id)
        if emp is None:
            raise NotFoundException(f"Сотрудник с id={payload.employee_id} не найден.")
        ind = await self._repo.get_indicator_by_id(payload.indicator_id)
        if ind is None:
            raise NotFoundException(f"Показатель с id={payload.indicator_id} не найден.")
        ev = await self._repo.create_employee_value(**payload.model_dump())
        return KPIEmployeeValueResponse.model_validate(ev)

    async def get_employee_values(
        self, employee_id: UUID, period_id: UUID
    ) -> list[KPIEmployeeValueResponse]:
        items = await self._repo.get_employee_values(employee_id, period_id)
        return [KPIEmployeeValueResponse.model_validate(v) for v in items]

    # ========================================================================
    # Calculation
    # ========================================================================

    async def calculate_employee(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> KPIEmployeeResult:
        """Calculate KPI for one employee in a given period.

        Collects:
        - Period-level values (KPIPeriod)
        - Employee-level values (KPIEmployeeValue)
        - Defect count (via DefectRepository)
        - Evaluates each indicator's formula
        """
        from app.modules.defects.repository import DefectRepository

        defect_repo = DefectRepository(self._session)

        # Get period values → dict[code, value]
        period_vals = await self._repo.get_period_values(payroll_period_id)
        period_dict: dict[str, Decimal] = {}
        for pv in period_vals:
            if pv.indicator:
                period_dict[pv.indicator.code] = pv.value

        # Get employee-specific values
        emp_vals = await self._repo.get_employee_values(employee_id, payroll_period_id)
        emp_dict: dict[str, Decimal] = {}
        for ev in emp_vals:
            if ev.indicator:
                emp_dict[ev.indicator.code] = ev.value

        # Get defect count
        defect_count = await defect_repo.count_by_employee_period(
            employee_id, payroll_period_id
        )

        # Build variable context
        variables: dict[str, Decimal] = {
            **period_dict,
            **emp_dict,
            "DEFECT_COUNT": Decimal(defect_count),
        }

        # Get active indicators and evaluate each
        indicators = await self._repo.get_active_indicators()
        results: dict[str, Decimal] = {}
        details: list[dict] = []

        total = Decimal("0")
        for ind in indicators:
            formula_obj = ind.formula
            if formula_obj is None:
                continue
            try:
                value = self._engine.evaluate(formula_obj.expression, variables)
            except FormulaError as e:
                details.append({
                    "indicator": ind.code,
                    "error": str(e),
                    "value": Decimal("0"),
                })
                continue

            # Store result
            await self._repo.upsert_employee_value(
                employee_id=employee_id,
                payroll_period_id=payroll_period_id,
                indicator_id=ind.id,
                value=value,
                source=KPISource.SYSTEM,
            )

            results[ind.code] = value
            total += value * ind.weight
            details.append({
                "indicator": ind.code,
                "name": ind.name,
                "weight": float(ind.weight),
                "formula": formula_obj.expression,
                "value": float(value),
                "weighted": float(value * ind.weight),
            })

        return KPIEmployeeResult(
            employee_id=employee_id,
            payroll_period_id=payroll_period_id,
            results=results,
            total_kpi=total,
            details=details,
        )

    async def recalculate_period(
        self, payroll_period_id: UUID
    ) -> list[KPIEmployeeResult]:
        """Recalculate KPI for ALL employees in a period."""
        # Get all employees who have KPI values in this period
        all_vals = await self._repo.get_all_employee_values(payroll_period_id)
        employee_ids = list({v.employee_id for v in all_vals})

        # Also get employees from department
        # For now, just recalculate those who already have values

        results: list[KPIEmployeeResult] = []
        for emp_id in employee_ids:
            result = await self.calculate_employee(emp_id, payroll_period_id)
            results.append(result)
        return results

    async def get_indicator_result(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> KPIEmployeeResult:
        """Get the latest calculated KPI result for an employee."""
        return await self.calculate_employee(employee_id, payroll_period_id)
