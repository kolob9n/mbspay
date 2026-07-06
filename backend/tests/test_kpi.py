"""Tests for KPI module — calculation and PayrollSourceProvider.

Run with:  pytest backend/tests/test_kpi.py -v
"""

from decimal import Decimal

import pytest

from app.shared.formula_engine import FormulaEngine
from app.shared.calculations.payroll_source_provider import PayrollSourceProvider


@pytest.fixture
def engine() -> FormulaEngine:
    return FormulaEngine()


# ============================================================================
# KPI formula evaluation via FormulaEngine (unit tests)
# ============================================================================


class TestKPIFormulas:
    """Test KPI formulas independently of database."""

    def test_kpi_without_defects(self, engine: FormulaEngine) -> None:
        """IF(DEFECT_COUNT = 0, 1, 0.85) — no defects → full coefficient."""
        formula = "IF(DEFECT_COUNT = 0, 1, 0.85)"
        result = engine.evaluate(formula, {"DEFECT_COUNT": 0})
        assert result == Decimal("1")

    def test_kpi_with_defects(self, engine: FormulaEngine) -> None:
        """IF(DEFECT_COUNT = 0, 1, 0.85) — 3 defects → reduced coefficient."""
        formula = "IF(DEFECT_COUNT = 0, 1, 0.85)"
        result = engine.evaluate(formula, {"DEFECT_COUNT": 3})
        assert result == Decimal("0.85")

    def test_kpi_plan_percent(self, engine: FormulaEngine) -> None:
        """PLAN_PERCENT / 100 — convert percentage to coefficient."""
        formula = "PLAN_PERCENT / 100"
        result = engine.evaluate(formula, {"PLAN_PERCENT": 95})
        assert result == Decimal("0.95")

    def test_kpi_salary_formula(self, engine: FormulaEngine) -> None:
        """SALARY * KPI_PERCENT / 100 * KPI_SHARE * KPI_COEF"""
        formula = "SALARY * KPI_PERCENT / 100 * KPI_SHARE * KPI_COEF"
        result = engine.evaluate(
            formula,
            {
                "SALARY": 100000,
                "KPI_PERCENT": 30,
                "KPI_SHARE": Decimal("1.0"),
                "KPI_COEF": Decimal("0.85"),
            },
        )
        assert result == Decimal("25500")

    def test_kpi_with_defect_coefficient(self, engine: FormulaEngine) -> None:
        """KPI_COEF changed after formula evaluation."""
        formula = "IF(DEFECT_COUNT > 2, 0.8, IF(DEFECT_COUNT > 0, 0.9, 1.0))"
        # 0 defects → 1.0
        assert engine.evaluate(formula, {"DEFECT_COUNT": 0}) == Decimal("1.0")
        # 1 defect → 0.9
        assert engine.evaluate(formula, {"DEFECT_COUNT": 1}) == Decimal("0.9")
        # 3 defects → 0.8
        assert engine.evaluate(formula, {"DEFECT_COUNT": 3}) == Decimal("0.8")

    def test_nested_if(self, engine: FormulaEngine) -> None:
        """Nested IF for multi-level KPI coefficients."""
        formula = "IF(DEFECT_COUNT = 0, 1, IF(DEFECT_COUNT <= 3, 0.85, 0.7))"
        assert engine.evaluate(formula, {"DEFECT_COUNT": 0}) == Decimal("1")
        assert engine.evaluate(formula, {"DEFECT_COUNT": 2}) == Decimal("0.85")
        assert engine.evaluate(formula, {"DEFECT_COUNT": 5}) == Decimal("0.7")


# ============================================================================
# Formula change tests
# ============================================================================


class TestFormulaChanges:
    """Test that changing formulas produces different results."""

    def test_old_formula_vs_new(self, engine: FormulaEngine) -> None:
        """Verify different formulas give different results with same data."""
        old_formula = "IF(DEFECT_COUNT = 0, 1, 0.85)"
        new_formula = "IF(DEFECT_COUNT = 0, 1, 0.9)"

        vars_ = {"DEFECT_COUNT": 2}
        old_result = engine.evaluate(old_formula, vars_)
        new_result = engine.evaluate(new_formula, vars_)
        assert old_result != new_result
        assert old_result == Decimal("0.85")
        assert new_result == Decimal("0.9")


# ============================================================================
# PayrollSourceProvider variable collection (unit-like)
# ============================================================================


class TestVariableCollection:
    """Test that variable collection logic produces correct dicts."""

    def test_expected_variable_names(self) -> None:
        """Verify the set of expected variables matches the spec."""
        expected = {
            "SALARY", "WORKED_DAYS", "WORKED_HOURS",
            "NORM_DAYS", "NORM_HOURS", "BASE_PERCENT",
            "KPI_PERCENT", "KPI_SHARE", "KPI_COEF",
            "BONUS", "PENALTY", "PAID", "OVERTIME_HOURS",
        }
        from app.shared.calculations.base import KNOWN_VARIABLES
        assert expected == KNOWN_VARIABLES

    def test_defect_count_variable(self, engine: FormulaEngine) -> None:
        """DEFECT_COUNT should be usable in formulas."""
        formula = "DEFECT_COUNT"
        result = engine.evaluate(formula, {"DEFECT_COUNT": 5})
        assert result == Decimal("5")


# ============================================================================
# Recalculation idempotency
# ============================================================================


class TestRecalculation:
    """Test that recalculation is idempotent."""

    def test_same_input_same_output(self, engine: FormulaEngine) -> None:
        """Same formula + same variables → same result every time."""
        formula = "IF(DEFECT_COUNT = 0, 1, 0.85)"
        variables = {"DEFECT_COUNT": 0}

        results = [engine.evaluate(formula, variables) for _ in range(5)]
        assert all(r == Decimal("1") for r in results)

    def test_different_input_different_output(self, engine: FormulaEngine) -> None:
        """Changing variable value changes result."""
        formula = "IF(DEFECT_COUNT = 0, 1, 0.85)"

        r1 = engine.evaluate(formula, {"DEFECT_COUNT": 0})
        r2 = engine.evaluate(formula, {"DEFECT_COUNT": 3})
        assert r1 != r2
