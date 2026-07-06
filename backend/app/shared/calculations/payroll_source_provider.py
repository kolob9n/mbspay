"""Payroll Source Provider — aggregates data from all modules for payroll calculation.

Collects employee values from:
- KPI module
- Defects module
- Timesheet module (future)
- Payments module (future)

Returns a unified variables dict ready for FormulaEngine.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class PayrollSourceProvider:
    """Unified data provider for payroll calculations.

    Aggregates KPI results, defect counts, timesheet data, etc.
    into a single variable dictionary consumed by the FormulaEngine.

    Usage::

        provider = PayrollSourceProvider(session)
        variables = await provider.get_employee_values(employee_id, period_id)
        # → {"KPI": 18500, "KPI_SHARE": 0.92, "KPI_COEF": 0.97, "DEFECT_COUNT": 1}
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_employee_values(
        self,
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> dict[str, Decimal]:
        """Collect all available variables for an employee in a period.

        Sources (in order of aggregation):
        0. Employee — salary, base data
        1. KPI — calculated values per indicator
        2. Defects — defect count per employee per period
        3. Payments — paid amount from ledger
        4. Timesheet — worked days, hours
        5. Calendar — norm days, hours
        """
        variables: dict[str, Decimal] = {}

        # ---- 0. Employee base data -----------------------------------------
        await self._collect_employee(variables, employee_id, payroll_period_id)

        # ---- 1. KPI values -------------------------------------------------
        await self._collect_kpi(variables, employee_id, payroll_period_id)

        # ---- 2. Defect count -----------------------------------------------
        await self._collect_defects(variables, employee_id, payroll_period_id)

        # ---- 3. Payments --------------------------------------------------
        await self._collect_payments(variables, employee_id, payroll_period_id)

        # ---- 4. Timesheet --------------------------------------------------
        await self._collect_timesheet(variables, employee_id, payroll_period_id)

        # ---- 5. Calendar norms ---------------------------------------------
        await self._collect_calendar(variables, employee_id, payroll_period_id)

        return variables

    # ---- Private collectors ------------------------------------------------

    async def _collect_kpi(
        self,
        variables: dict[str, Decimal],
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> None:
        """Collect calculated KPI values."""
        from app.modules.kpi.repository import KPIRepository

        kpi_repo = KPIRepository(self._session)
        values = await kpi_repo.get_employee_values(employee_id, payroll_period_id)

        for v in values:
            if v.indicator:
                variables[v.indicator.code] = v.value

        # Compute aggregate KPI value
        kpi_total = sum((v.value for v in values), Decimal("0"))
        variables["KPI"] = kpi_total

        # KPI_SHARE and KPI_COEF from period-level values
        period_values = await kpi_repo.get_period_values(payroll_period_id)
        for pv in period_values:
            if pv.indicator and pv.indicator.code in ("KPI_SHARE", "KPI_COEF"):
                variables[pv.indicator.code] = pv.value

    async def _collect_defects(
        self,
        variables: dict[str, Decimal],
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> None:
        """Collect defect count."""
        from app.modules.defects.repository import DefectRepository

        defect_repo = DefectRepository(self._session)
        count = await defect_repo.count_by_employee_period(
            employee_id, payroll_period_id
        )
        variables["DEFECT_COUNT"] = Decimal(count)

        # Also provide per-type counts
        by_type = await defect_repo.count_by_employee_period_by_type(
            employee_id, payroll_period_id
        )
        for type_code, cnt in by_type.items():
            variables[f"DEFECT_{type_code}"] = Decimal(cnt)

    async def _collect_employee(
        self,
        variables: dict[str, Decimal],
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> None:
        """Collect base employee data: SALARY."""
        from app.modules.employees.repository import EmployeeRepository

        emp_repo = EmployeeRepository(self._session)
        emp = await emp_repo.get_by_id(employee_id)
        if emp is not None:
            variables["SALARY"] = emp.salary

    async def _collect_payments(
        self,
        variables: dict[str, Decimal],
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> None:
        """Collect payment data from ledger."""
        from app.modules.payroll_ledger.repository import PayrollLedgerRepository

        ledger_repo = PayrollLedgerRepository(self._session)
        accrued, paid, balance = await ledger_repo.calculate_balance(
            employee_id, payroll_period_id
        )
        variables["PAID"] = paid

    async def _collect_timesheet(
        self,
        variables: dict[str, Decimal],
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> None:
        """Collect timesheet data: WORKED_DAYS, WORKED_HOURS."""
        from app.modules.timesheets.repository import TimesheetRepository

        timesheet_repo = TimesheetRepository(self._session)
        summary = await timesheet_repo.calculate_summary_for_employee(
            employee_id, payroll_period_id
        )
        variables["WORKED_DAYS"] = Decimal(summary.get("worked_days", 0))
        variables["WORKED_HOURS"] = Decimal(summary.get("worked_hours", 0))

    async def _collect_calendar(
        self,
        variables: dict[str, Decimal],
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> None:
        """Collect calendar norms: NORM_DAYS, NORM_HOURS."""
        from app.modules.payroll_periods.repository import PayrollPeriodRepository
        from app.modules.calendar.repository import CalendarRepository

        period_repo = PayrollPeriodRepository(self._session)
        period = await period_repo.get_by_id(payroll_period_id)
        if period is None:
            return

        cal_repo = CalendarRepository(self._session)
        cal_year = await cal_repo.get_year_by_number(period.year)
        if cal_year is not None:
            wd, wh = await cal_repo.calculate_month_norm(cal_year.id, period.month)
            variables["NORM_DAYS"] = Decimal(wd)
            variables["NORM_HOURS"] = Decimal(wh)

    # ---- Public helpers ----------------------------------------------------

    async def get_payment_data(
        self,
        employee_id: UUID,
        payroll_period_id: UUID,
    ) -> dict[str, Decimal]:
        """Return only payment-related variables for payroll calculation."""
        variables: dict[str, Decimal] = {}
        await self._collect_payments(variables, employee_id, payroll_period_id)
        return variables
