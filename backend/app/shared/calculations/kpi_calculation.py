"""KPI calculation — stub.

Will use FormulaEngine to compute KPI-based bonuses.
"""

from app.shared.calculations.base import CalculationContext, CalculationResult, CalculationService


class KPICalculationService(CalculationService):
    """Stub — will evaluate KPI formulas against employee metrics."""

    async def calculate(self, context: CalculationContext) -> CalculationResult:
        return CalculationResult(
            success=True,
            value=None,
            details={"message": "KPICalculationService — not implemented yet"},
        )
