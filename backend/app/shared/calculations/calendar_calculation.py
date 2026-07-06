"""Calendar calculation — stub.

Will compute working days/hours norms from the production calendar.
"""

from app.shared.calculations.base import CalculationContext, CalculationResult, CalculationService


class CalendarCalculationService(CalculationService):
    """Stub — will use CalendarRepository to compute month norms."""

    async def calculate(self, context: CalculationContext) -> CalculationResult:
        return CalculationResult(
            success=True,
            value=None,
            details={"message": "CalendarCalculationService — not implemented yet"},
        )
