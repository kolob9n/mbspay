"""Payroll service — orchestrates payroll calculation across all modules."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.repository import EmployeeRepository
from app.modules.formula_engine.repository import FormulaRepository
from app.modules.payroll.models import PayrollRunStatus
from app.modules.payroll.repository import PayrollRepository
from app.modules.payroll.schemas import (
    PayrollResultResponse,
    PayrollRunCreate,
    PayrollRunDetailResponse,
    PayrollRunResponse,
)
from app.shared.calculations.payroll_source_provider import PayrollSourceProvider
from app.shared.exceptions import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
)
from app.shared.formula_engine import FormulaEngine, FormulaError


class PayrollService:
    """Orchestrates payroll calculation.

    Collects data via PayrollSourceProvider → evaluates via FormulaEngine →
    stores PayrollResult with formula_snapshot.

    Does NOT contain hardcoded formulas — all formulas are in FormulaEngine.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PayrollRepository(session)
        self._emp_repo = EmployeeRepository(session)
        self._formula_repo = FormulaRepository(session)
        self._provider = PayrollSourceProvider(session)
        self._engine = FormulaEngine()

    # ========================================================================
    # Create run
    # ========================================================================

    async def create_run(
        self,
        payload: PayrollRunCreate,
        *,
        created_by: UUID | None = None,
    ) -> PayrollRunResponse:
        # Determine version
        last = await self._repo.get_last_version(payload.payroll_period_id)
        version = (last.version + 1) if last else 1

        # Generate number: PR-YYYYMM-vN
        now = datetime.now(timezone.utc)
        number = f"PR-{now.strftime('%Y%m')}-v{version}"

        run = await self._repo.create_run(
            number=number,
            payroll_period_id=payload.payroll_period_id,
            version=version,
            created_by=created_by,
        )
        return PayrollRunResponse.model_validate(run)

    # ========================================================================
    # Calculate
    # ========================================================================

    async def run_calculation(self, run_id: UUID) -> PayrollRunDetailResponse:
        run = await self._repo.get_by_id(run_id)
        if run is None:
            raise NotFoundException(f"Расчёт с id={run_id} не найден.")

        if run.status not in (PayrollRunStatus.DRAFT, PayrollRunStatus.CALCULATED):
            raise BusinessRuleException(
                f"Нельзя запустить расчёт в статусе {run.status.value}."
            )

        # Clear previous results (allows recalculation of same version)
        await self._repo.clear_results(run_id)

        # Get active employees
        employees, _ = await self._emp_repo.get_all(
            is_active=True, limit=10_000
        )

        # Get formulas
        base_formula = await self._formula_repo.get_by_code("BASE_SALARY")
        kpi_formula = await self._formula_repo.get_by_code("KPI")
        total_formula = await self._formula_repo.get_by_code("TOTAL")

        results_count = 0
        for emp in employees:
            await self._calculate_employee(
                run_id=run_id,
                employee_id=emp.id,
                payroll_period_id=run.payroll_period_id,
                base_formula_expr=base_formula.expression if base_formula else None,
                kpi_formula_expr=kpi_formula.expression if kpi_formula else None,
                total_formula_expr=total_formula.expression if total_formula else None,
            )
            results_count += 1

        run.status = PayrollRunStatus.CALCULATED
        run.calculation_date = datetime.now(timezone.utc)
        await self._session.flush()

        return await self._get_detail(run_id)

    async def _calculate_employee(
        self,
        *,
        run_id: UUID,
        employee_id: UUID,
        payroll_period_id: UUID,
        base_formula_expr: str | None,
        kpi_formula_expr: str | None,
        total_formula_expr: str | None,
    ) -> None:
        """Calculate payroll for one employee."""

        # 1. Collect ALL variables from all sources
        variables = await self._provider.get_employee_values(
            employee_id, payroll_period_id
        )

        # Default variable values
        salary = variables.get("SALARY", Decimal("0"))
        worked_days = int(variables.get("WORKED_DAYS", 0))
        worked_hours = int(variables.get("WORKED_HOURS", 0))
        norm_days = int(variables.get("NORM_DAYS", 0))
        norm_hours = int(variables.get("NORM_HOURS", 0))
        bonus = variables.get("BONUS", Decimal("0"))
        penalty = variables.get("PENALTY", Decimal("0"))
        paid = variables.get("PAID", Decimal("0"))
        overtime_val = variables.get("OVERTIME_HOURS", Decimal("0"))
        kpi_share = variables.get("KPI_SHARE", Decimal("0"))
        kpi_coef = variables.get("KPI_COEF", Decimal("0"))
        base_percent = variables.get("BASE_PERCENT", Decimal("55"))
        kpi_percent = variables.get("KPI_PERCENT", Decimal("30"))

        # 2. Compute BASE_SALARY
        base_salary = Decimal("0")
        if base_formula_expr:
            try:
                base_salary = self._engine.evaluate(base_formula_expr, {
                    "SALARY": salary,
                    "BASE_PERCENT": base_percent,
                    "NORM_DAYS": Decimal(norm_days),
                    "WORKED_DAYS": Decimal(worked_days),
                })
            except FormulaError:
                base_salary = Decimal("0")

        # 3. Compute KPI
        kpi_val = Decimal("0")
        if kpi_formula_expr:
            try:
                kpi_val = self._engine.evaluate(kpi_formula_expr, {
                    "SALARY": salary,
                    "KPI_PERCENT": kpi_percent,
                    "KPI_SHARE": kpi_share,
                    "KPI_COEF": kpi_coef,
                })
            except FormulaError:
                kpi_val = Decimal("0")

        # 4. Compute TOTAL (total accrual)
        total = base_salary + kpi_val + bonus + overtime_val - penalty

        # 5. Compute BALANCE (total - already paid)
        balance = total - paid

        # 6. Compute FINAL (if TOTAL formula exists, use it)
        # TOTAL formula: BASE+KPI+BONUS+OVERTIME-PENALTY-PAID
        if total_formula_expr:
            try:
                final = self._engine.evaluate(total_formula_expr, {
                    "BASE": base_salary,
                    "KPI": kpi_val,
                    "BONUS": bonus,
                    "OVERTIME": overtime_val,
                    "PENALTY": penalty,
                    "PAID": paid,
                })
            except FormulaError:
                final = total
        else:
            final = balance

        # 7. Build formula_snapshot
        snapshot = {
            "formulas": {
                "BASE_SALARY": base_formula_expr,
                "KPI": kpi_formula_expr,
                "TOTAL": total_formula_expr,
            },
            "variables": {k: float(v) for k, v in variables.items()},
            "intermediate": {
                "base_salary": float(base_salary),
                "kpi": float(kpi_val),
                "total": float(total),
                "balance": float(balance),
                "final": float(final),
            },
            "calculation_date": datetime.now(timezone.utc).isoformat(),
        }

        # 8. Save PayrollResult
        await self._repo.create_result(
            payroll_run_id=run_id,
            employee_id=employee_id,
            salary=salary,
            worked_days=worked_days,
            worked_hours=worked_hours,
            norm_days=norm_days,
            norm_hours=norm_hours,
            base_salary=base_salary,
            kpi=kpi_val,
            bonus=bonus,
            penalty=penalty,
            overtime=overtime_val,
            paid=paid,
            total=total,
            balance=balance,
            formula_snapshot=snapshot,
        )

    # ========================================================================
    # Read
    # ========================================================================

    async def get_all(
        self,
        *,
        payroll_period_id: UUID | None = None,
        status: PayrollRunStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[PayrollRunResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(
            payroll_period_id=payroll_period_id,
            status=status,
            offset=offset,
            limit=size,
        )
        return [PayrollRunResponse.model_validate(r) for r in items]

    async def get_by_id(self, run_id: UUID) -> PayrollRunDetailResponse:
        return await self._get_detail(run_id)

    async def get_results(self, run_id: UUID) -> list[PayrollResultResponse]:
        results = await self._repo.get_results(run_id)
        return [PayrollResultResponse.model_validate(r) for r in results]

    async def get_employee_result(
        self, run_id: UUID, employee_id: UUID
    ) -> PayrollResultResponse:
        result = await self._repo.get_employee_result(run_id, employee_id)
        if result is None:
            raise NotFoundException(
                f"Результат расчёта для сотрудника {employee_id} не найден."
            )
        return PayrollResultResponse.model_validate(result)

    # ========================================================================
    # Approve → create ACCRUAL in PayrollLedger
    # ========================================================================

    async def approve(self, run_id: UUID) -> PayrollRunDetailResponse:
        run = await self._repo.get_by_id(run_id, with_results=True)
        if run is None:
            raise NotFoundException(f"Расчёт с id={run_id} не найден.")

        if run.status != PayrollRunStatus.CALCULATED:
            raise BusinessRuleException(
                f"Нельзя утвердить расчёт в статусе {run.status.value}."
            )

        # Idempotency: only create ledger entries once
        already_accrued = await self._repo.has_accrued(run_id)
        if not already_accrued:
            from app.modules.payroll_ledger.repository import PayrollLedgerRepository
            from app.modules.payroll_ledger.models import DocumentType, OperationType

            ledger_repo = PayrollLedgerRepository(self._session)
            now = datetime.now(timezone.utc)

            for result in run.results:
                await ledger_repo.create_entry(
                    employee_id=result.employee_id,
                    payroll_period_id=run.payroll_period_id,
                    document_type=DocumentType.PAYROLL,
                    document_id=run.id,
                    operation_type=OperationType.ACCRUAL,
                    amount=result.total,
                    operation_date=now,
                )

        await self._repo.approve(run)
        return await self._get_detail(run_id)

    # ========================================================================
    # Close / Cancel
    # ========================================================================

    async def close(self, run_id: UUID) -> PayrollRunDetailResponse:
        run = await self._repo.get_by_id(run_id)
        if run is None:
            raise NotFoundException(f"Расчёт с id={run_id} не найден.")
        if run.status != PayrollRunStatus.APPROVED:
            raise BusinessRuleException(
                f"Нельзя закрыть расчёт в статусе {run.status.value}."
            )
        await self._repo.close(run)
        return await self._get_detail(run_id)

    async def cancel(self, run_id: UUID) -> PayrollRunDetailResponse:
        run = await self._repo.get_by_id(run_id)
        if run is None:
            raise NotFoundException(f"Расчёт с id={run_id} не найден.")
        if run.status in (PayrollRunStatus.CLOSED, PayrollRunStatus.CANCELLED):
            raise BusinessRuleException(
                f"Нельзя отменить расчёт в статусе {run.status.value}."
            )
        await self._repo.cancel(run)
        return await self._get_detail(run_id)

    # ========================================================================
    # Helpers
    # ========================================================================

    async def _get_detail(self, run_id: UUID) -> PayrollRunDetailResponse:
        run = await self._repo.get_by_id(run_id, with_results=True)
        if run is None:
            raise NotFoundException(f"Расчёт с id={run_id} не найден.")

        results = await self._repo.get_results(run_id)
        total_amount = sum((r.total for r in results), Decimal("0"))

        return PayrollRunDetailResponse(
            id=run.id,
            number=run.number,
            payroll_period_id=run.payroll_period_id,
            status=run.status,
            version=run.version,
            calculation_date=run.calculation_date,
            formula_version=run.formula_version,
            created_by=run.created_by,
            created_at=run.created_at,
            updated_at=run.updated_at,
            approved_at=run.approved_at,
            results=[PayrollResultResponse.model_validate(r) for r in results],
            employee_count=len(results),
            total_amount=total_amount,
        )
