"""Payroll Workspace service — orchestrates the accountant's workflow."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payroll_workspace.repository import WorkspaceRepository
from app.modules.payroll_workspace.schemas import (
    ActionResponse,
    KPIStatusResponse,
    ModuleStatus,
    PaymentStatusResponse,
    PayrollStatusResponse,
    WorkspaceError,
    WorkspaceStatusResponse,
)
from app.shared.exceptions import BusinessRuleException, NotFoundException


class PayrollWorkspaceService:
    """Single-screen orchestrator for the accountant's monthly workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WorkspaceRepository(session)

    async def get_period_status(
        self, period_id: UUID
    ) -> WorkspaceStatusResponse:
        from app.modules.payroll_periods.repository import PayrollPeriodRepository
        period_repo = PayrollPeriodRepository(self._session)
        period = await period_repo.get_by_id(period_id)
        if period is None:
            raise NotFoundException(f"Период с id={period_id} не найден.")

        calendar_ok = await self._repo.has_approved_calendar(period.year)
        timesheets_ok = await self._repo.has_approved_timesheets(period_id)
        kpi_ok = await self._repo.has_kpi_calculated(period_id)
        payments_ok = await self._repo.has_payments_posted(period_id)
        payroll_ok = await self._repo.has_payroll_approved(period_id)

        errors_raw = await self._repo.get_errors(period_id)
        errors = [WorkspaceError(**e) for e in errors_raw]

        return WorkspaceStatusResponse(
            period_id=period.id,
            period_label=period.period_label,
            period_status=period.status.value if hasattr(period.status, 'value') else str(period.status),
            modules=ModuleStatus(
                calendar=calendar_ok,
                timesheets=timesheets_ok,
                kpi=kpi_ok,
                payments=payments_ok,
                payroll=payroll_ok,
                payslips=payroll_ok,
                closed=period.status.value == "CLOSED" if hasattr(period.status, 'value') else False,
            ),
            errors=errors,
        )

    async def get_kpi_status(self, period_id: UUID) -> KPIStatusResponse:
        total, calculated, errors = await self._repo.get_kpi_stats(period_id)
        return KPIStatusResponse(
            period_id=period_id,
            total_employees=total,
            calculated=calculated,
            errors=errors,
            indicators=[],
        )

    async def get_payment_status(self, period_id: UUID) -> PaymentStatusResponse:
        count, total, emp_count, last_date = await self._repo.get_payment_stats(period_id)
        return PaymentStatusResponse(
            period_id=period_id,
            documents_count=count,
            total_amount=total,
            total_employees=emp_count,
            last_import_date=last_date,
        )

    async def get_payroll_status(self, period_id: UUID) -> PayrollStatusResponse:
        accrued, paid, balance, emp_count, run_id, run_status = await self._repo.get_payroll_stats(period_id)
        return PayrollStatusResponse(
            period_id=period_id,
            has_active_run=run_id is not None,
            run_id=UUID(run_id) if run_id else None,
            run_status=run_status,
            total_accrued=accrued,
            total_paid=paid,
            total_balance=balance,
            total_employees=emp_count,
        )

    async def get_errors(self, period_id: UUID) -> list[WorkspaceError]:
        errors_raw = await self._repo.get_errors(period_id)
        return [WorkspaceError(**e) for e in errors_raw]

    async def calculate_kpi(self, period_id: UUID) -> ActionResponse:
        from app.modules.kpi.service import KPIService
        kpi_service = KPIService(self._session)
        results = await kpi_service.recalculate_period(period_id)
        return ActionResponse(
            success=True,
            message=f"KPI рассчитан для {len(results)} сотрудников",
            data={"calculated": len(results)},
        )

    async def calculate_payroll(self, period_id: UUID) -> ActionResponse:
        from app.modules.payroll.repository import PayrollRepository
        from app.modules.payroll.service import PayrollService
        payroll_repo = PayrollRepository(self._session)
        last = await payroll_repo.get_last_version(period_id)

        payroll_service = PayrollService(self._session)
        if last and last.status.value in ("DRAFT", "CALCULATED"):
            run = await payroll_service.run_calculation(last.id)
        else:
            from app.modules.payroll.schemas import PayrollRunCreate
            run_create = PayrollRunCreate(payroll_period_id=period_id)
            run_resp = await payroll_service.create_run(run_create)
            run = await payroll_service.run_calculation(run_resp.id)

        return ActionResponse(
            success=True,
            message=f"Расчёт выполнен, версия {run.version}",
            data={"run_id": str(run.id), "version": run.version},
        )

    async def approve_payroll(self, period_id: UUID) -> ActionResponse:
        from app.modules.payroll.repository import PayrollRepository
        from app.modules.payroll.service import PayrollService
        payroll_repo = PayrollRepository(self._session)
        last = await payroll_repo.get_last_version(period_id)
        if last is None:
            raise BusinessRuleException("Нет рассчитанного PayrollRun для утверждения.")
        payroll_service = PayrollService(self._session)
        run = await payroll_service.approve(last.id)
        return ActionResponse(success=True, message=f"Расчёт утверждён", data={"run_id": str(run.id)})

    async def close_period(self, period_id: UUID) -> ActionResponse:
        from app.modules.payroll_periods.repository import PayrollPeriodRepository
        period_repo = PayrollPeriodRepository(self._session)
        period = await period_repo.get_by_id(period_id)
        if period is None:
            raise NotFoundException("Период не найден.")
        await period_repo.close(period)
        return ActionResponse(success=True, message="Месяц закрыт.")
