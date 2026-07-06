"""Timesheet calculation — stub.

Will aggregate timesheet entries for payroll input.
"""

from app.shared.calculations.base import CalculationContext, CalculationResult, CalculationService


class TimesheetCalculationService(CalculationService):
    """Stub — will use TimesheetRepository to compute worked days/hours."""

    async def calculate(self, context: CalculationContext) -> CalculationResult:
        return CalculationResult(
            success=True,
            value=None,
            details={"message": "TimesheetCalculationService — not implemented yet"},
        )
