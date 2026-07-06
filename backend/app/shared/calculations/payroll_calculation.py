"""Payroll calculation — stub.

Will orchestrate Calendar + Timesheet + KPI → final salary.
"""

from app.shared.calculations.base import CalculationContext, CalculationResult, CalculationService


class PayrollCalculationService(CalculationService):
    """Stub — will compose CalendarCalculation + TimesheetCalculation + FormulaEngine."""

    async def calculate(self, context: CalculationContext) -> CalculationResult:
        return CalculationResult(
            success=True,
            value=None,
            details={"message": "PayrollCalculationService — not implemented yet"},
        )
