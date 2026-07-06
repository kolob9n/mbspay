"""Calculation Engine — abstraction layer for all payroll calculations.

Defines common interfaces used by:
- calendar_calculation
- timesheet_calculation
- kpi_calculation
- payroll_calculation
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID


# ---- Context ---------------------------------------------------------------


@dataclass
class CalculationContext:
    """Input data for any calculation.

    Concrete calculation types extend this with specific fields.
    """

    employee_id: UUID
    payroll_period_id: UUID
    variables: dict[str, Decimal] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---- Result ----------------------------------------------------------------


@dataclass
class CalculationResult:
    """Output of any calculation."""

    success: bool
    value: Decimal | None = None
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


# ---- Service (abstract) ----------------------------------------------------


class CalculationService:
    """Base class for all calculation services.

    Subclasses override ``calculate()`` with domain-specific logic.
    """

    async def calculate(self, context: CalculationContext) -> CalculationResult:
        raise NotImplementedError


# ---- Variable definitions --------------------------------------------------

# Canonical list of supported variables for the formula engine.
# New variables can be added here without changing the engine core.

KNOWN_VARIABLES: set[str] = {
    "SALARY",
    "WORKED_DAYS",
    "WORKED_HOURS",
    "NORM_DAYS",
    "NORM_HOURS",
    "BASE_PERCENT",
    "KPI_PERCENT",
    "KPI_SHARE",
    "KPI_COEF",
    "BONUS",
    "PENALTY",
    "PAID",
    "OVERTIME_HOURS",
}
