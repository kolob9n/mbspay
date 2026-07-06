"""Payroll Workspace repository — aggregates readiness checks."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_approved_calendar(self, year: int) -> bool:
        from app.modules.calendar.models import CalendarYear, YearStatus
        stmt = select(func.count(CalendarYear.id)).where(
            CalendarYear.year == year,
            CalendarYear.status == YearStatus.APPROVED,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def has_approved_timesheets(
        self, payroll_period_id: UUID
    ) -> bool:
        from app.modules.timesheets.models import Timesheet, TimesheetStatus
        stmt = select(func.count(Timesheet.id)).where(
            Timesheet.payroll_period_id == payroll_period_id,
            Timesheet.status.in_(
                [TimesheetStatus.APPROVED, TimesheetStatus.CLOSED]
            ),
        )
        result = await self._session.execute(stmt)
        total_stmt = select(func.count(Timesheet.id)).where(
            Timesheet.payroll_period_id == payroll_period_id,
        )
        total = (await self._session.execute(total_stmt)).scalar_one()
        approved = result.scalar_one()
        return total > 0 and approved == total

    async def has_kpi_calculated(self, payroll_period_id: UUID) -> bool:
        from app.modules.kpi.models import KPIEmployeeValue
        stmt = select(func.count(KPIEmployeeValue.id)).where(
            KPIEmployeeValue.payroll_period_id == payroll_period_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def has_payments_posted(self, payroll_period_id: UUID) -> bool:
        from app.modules.payroll_ledger.models import PayrollLedgerEntry, OperationType
        stmt = select(func.count(PayrollLedgerEntry.id)).where(
            PayrollLedgerEntry.payroll_period_id == payroll_period_id,
            PayrollLedgerEntry.operation_type == OperationType.PAYMENT,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def has_payroll_approved(self, payroll_period_id: UUID) -> bool:
        from app.modules.payroll.models import PayrollRun, PayrollRunStatus
        stmt = select(func.count(PayrollRun.id)).where(
            PayrollRun.payroll_period_id == payroll_period_id,
            PayrollRun.status == PayrollRunStatus.APPROVED,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def get_kpi_stats(
        self, payroll_period_id: UUID
    ) -> tuple[int, int, int]:
        from app.modules.employees.models import Employee
        from app.modules.kpi.models import KPIEmployeeValue
        total_emps = (await self._session.execute(
            select(func.count(Employee.id)).where(Employee.is_active == True)
        )).scalar_one()
        calculated = (await self._session.execute(
            select(func.count(KPIEmployeeValue.id)).where(
                KPIEmployeeValue.payroll_period_id == payroll_period_id,
            )
        )).scalar_one()
        errors = 0  # future: count errors from formula_snapshot
        return total_emps, calculated, errors

    async def get_payment_stats(
        self, payroll_period_id: UUID
    ) -> tuple[int, Decimal, int, Optional[str]]:
        from app.modules.payments.models import Payment, PaymentItem, PaymentStatus
        stmt = select(func.count(Payment.id)).where(
            Payment.payroll_period_id == payroll_period_id,
            Payment.status == PaymentStatus.POSTED,
        )
        count = (await self._session.execute(stmt)).scalar_one()
        # total amount
        amt_stmt = select(func.coalesce(func.sum(PaymentItem.amount), 0)).join(
            Payment, PaymentItem.payment_id == Payment.id
        ).where(
            Payment.payroll_period_id == payroll_period_id,
            Payment.status == PaymentStatus.POSTED,
        )
        total = (await self._session.execute(amt_stmt)).scalar_one()
        # distinct employees
        emp_stmt = select(func.count(func.distinct(PaymentItem.employee_id))).join(
            Payment, PaymentItem.payment_id == Payment.id
        ).where(
            Payment.payroll_period_id == payroll_period_id,
            Payment.status == PaymentStatus.POSTED,
        )
        emp_count = (await self._session.execute(emp_stmt)).scalar_one()
        # last import date
        last_stmt = select(Payment.created_at).where(
            Payment.payroll_period_id == payroll_period_id,
        ).order_by(Payment.created_at.desc()).limit(1)
        last_res = await self._session.execute(last_stmt)
        last_date = last_res.scalar_one_or_none()
        return count, Decimal(str(total)), emp_count, str(last_date) if last_date else None

    async def get_payroll_stats(
        self, payroll_period_id: UUID
    ) -> tuple[Decimal, Decimal, Decimal, int, Optional[str], Optional[str]]:
        from app.modules.payroll.models import PayrollResult, PayrollRun, PayrollRunStatus
        stmt = select(PayrollRun).where(
            PayrollRun.payroll_period_id == payroll_period_id,
        ).order_by(PayrollRun.version.desc()).limit(1)
        res = await self._session.execute(stmt)
        run = res.scalar_one_or_none()
        if run is None:
            return Decimal("0"), Decimal("0"), Decimal("0"), 0, None, None
        total_accrued = Decimal("0")
        total_paid = Decimal("0")
        total_balance = Decimal("0")
        results = (await self._session.execute(
            select(PayrollResult).where(PayrollResult.payroll_run_id == run.id)
        )).scalars().all()
        emp_count = len(results)
        for r in results:
            total_accrued += r.total
            total_paid += r.paid
            total_balance += r.balance
        return total_accrued, total_paid, total_balance, emp_count, str(run.id), run.status.value if run.status else None

    async def get_errors(
        self, payroll_period_id: UUID
    ) -> list[dict]:
        errors: list[dict] = []
        from app.modules.payroll_periods.repository import PayrollPeriodRepository
        period_repo = PayrollPeriodRepository(self._session)
        period = await period_repo.get_by_id(payroll_period_id)
        if period is None:
            return errors

        # Check calendar
        from app.modules.calendar.models import CalendarYear, YearStatus
        cal_stmt = select(CalendarYear).where(
            CalendarYear.year == period.year,
            CalendarYear.status == YearStatus.APPROVED,
        )
        cal_res = await self._session.execute(cal_stmt)
        if cal_res.scalar_one_or_none() is None:
            errors.append({"code": "NO_CALENDAR", "message": f"Производственный календарь на {period.year} год не утверждён", "module": "calendar"})

        # Check unapproved timesheets
        from app.modules.timesheets.models import Timesheet, TimesheetStatus
        ts_stmt = select(Timesheet).where(
            Timesheet.payroll_period_id == payroll_period_id,
            Timesheet.status.notin_([TimesheetStatus.APPROVED, TimesheetStatus.CLOSED]),
        )
        ts_res = await self._session.execute(ts_stmt)
        for ts in ts_res.scalars().all():
            errors.append({"code": "UNAPPROVED_TIMESHEET", "message": f"Не утверждён табель подразделения (id={ts.department_id})", "module": "timesheets", "entity_id": str(ts.id)})

        # Check employees without work schedule
        from app.modules.employees.models import Employee
        emp_stmt = select(Employee).where(
            Employee.is_active == True,
            Employee.work_schedule_id == None,
        )
        emp_res = await self._session.execute(emp_stmt)
        for emp in emp_res.scalars().all():
            errors.append({"code": "NO_SCHEDULE", "message": f"У сотрудника {emp.full_name} отсутствует график работы", "module": "employees", "entity_id": str(emp.id)})

        return errors
