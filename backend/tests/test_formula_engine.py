"""Tests for Formula Engine — safe mathematical expression interpreter.

Run with:  pytest backend/tests/test_formula_engine.py -v
"""

from decimal import Decimal

import pytest

from app.shared.formula_engine import FormulaEngine
from app.shared.formula_engine.exceptions import (
    DivisionByZeroError,
    FormulaSyntaxError,
    UnknownVariableError,
)


@pytest.fixture
def engine() -> FormulaEngine:
    return FormulaEngine()


# ============================================================================
# Basic arithmetic
# ============================================================================


class TestBasicArithmetic:
    def test_addition(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("2 + 3", {}) == Decimal("5")

    def test_subtraction(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("10 - 4", {}) == Decimal("6")

    def test_multiplication(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("6 * 7", {}) == Decimal("42")

    def test_division(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("100 / 4", {}) == Decimal("25")

    def test_decimal_division(self, engine: FormulaEngine) -> None:
        result = engine.evaluate("10 / 3", {})
        assert abs(result - Decimal("3.333333333333333333333333333")) < Decimal("0.01")

    def test_operator_precedence(self, engine: FormulaEngine) -> None:
        # 2 + 3 * 4 = 14 (not 20)
        assert engine.evaluate("2 + 3 * 4", {}) == Decimal("14")

    def test_parentheses_override(self, engine: FormulaEngine) -> None:
        # (2 + 3) * 4 = 20
        assert engine.evaluate("(2 + 3) * 4", {}) == Decimal("20")

    def test_nested_parentheses(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("((2 + 3) * (4 - 1)) / 5", {}) == Decimal("3")

    def test_unary_minus(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("-5 + 3", {}) == Decimal("-2")

    def test_unary_minus_expression(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("-(3 + 2)", {}) == Decimal("-5")


# ============================================================================
# Variables
# ============================================================================


class TestVariables:
    def test_single_variable(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("SALARY", {"SALARY": 100000}) == Decimal("100000")

    def test_variable_in_expression(self, engine: FormulaEngine) -> None:
        result = engine.evaluate(
            "SALARY * 2 + BONUS",
            {"SALARY": 50000, "BONUS": 10000},
        )
        assert result == Decimal("110000")

    def test_missing_variable(self, engine: FormulaEngine) -> None:
        with pytest.raises(UnknownVariableError) as exc:
            engine.evaluate("SALARY + UNKNOWN", {"SALARY": 100})
        assert "UNKNOWN" in str(exc.value)

    def test_get_variables(self, engine: FormulaEngine) -> None:
        vars_ = engine.get_variables("SALARY * BASE_PERCENT + BONUS - PENALTY")
        assert vars_ == ["BASE_PERCENT", "BONUS", "PENALTY", "SALARY"]


# ============================================================================
# Functions
# ============================================================================


class TestFunctions:
    def test_round_up(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("ROUND(3.7)", {}) == Decimal("4")

    def test_round_down(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("ROUND(3.2)", {}) == Decimal("3")

    def test_abs_positive(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("ABS(5)", {}) == Decimal("5")

    def test_abs_negative(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("ABS(-7)", {}) == Decimal("7")

    def test_min(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("MIN(5, 3, 8, 1)", {}) == Decimal("1")

    def test_min_two(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("MIN(10, 20)", {}) == Decimal("10")

    def test_max(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("MAX(5, 3, 8, 1)", {}) == Decimal("8")

    def test_if_true(self, engine: FormulaEngine) -> None:
        # condition non-zero → true branch
        assert engine.evaluate("IF(1, 100, 200)", {}) == Decimal("100")

    def test_if_false(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("IF(0, 100, 200)", {}) == Decimal("200")

    def test_if_with_variable(self, engine: FormulaEngine) -> None:
        assert engine.evaluate(
            "IF(KPI_COEF, BONUS, 0)",
            {"KPI_COEF": Decimal("0.8"), "BONUS": Decimal("15000")},
        ) == Decimal("15000")


# ============================================================================
# Complex formulas (real-world)
# ============================================================================


class TestComplexFormulas:
    def test_base_salary_formula(self, engine: FormulaEngine) -> None:
        """(SALARY * BASE_PERCENT / 100 / NORM_DAYS) * WORKED_DAYS"""
        result = engine.evaluate(
            "(SALARY * BASE_PERCENT / 100 / NORM_DAYS) * WORKED_DAYS",
            {
                "SALARY": Decimal("100000"),
                "BASE_PERCENT": Decimal("55"),
                "NORM_DAYS": Decimal("22"),
                "WORKED_DAYS": Decimal("20"),
            },
        )
        assert result == Decimal("50000")

    def test_kpi_formula(self, engine: FormulaEngine) -> None:
        """SALARY * KPI_PERCENT / 100 * KPI_SHARE * KPI_COEF"""
        result = engine.evaluate(
            "SALARY * KPI_PERCENT / 100 * KPI_SHARE * KPI_COEF",
            {
                "SALARY": Decimal("100000"),
                "KPI_PERCENT": Decimal("30"),
                "KPI_SHARE": Decimal("1"),
                "KPI_COEF": Decimal("0.85"),
            },
        )
        # 100000 * 0.30 * 1 * 0.85 = 25500
        assert result == Decimal("25500")


# ============================================================================
# Validation
# ============================================================================


class TestValidation:
    def test_valid_formula(self, engine: FormulaEngine) -> None:
        assert engine.validate("SALARY * 2 + BONUS") == []

    def test_invalid_syntax_missing_operand(self, engine: FormulaEngine) -> None:
        errors = engine.validate("SALARY +")
        assert len(errors) > 0

    def test_invalid_syntax_unmatched_paren(self, engine: FormulaEngine) -> None:
        errors = engine.validate("(SALARY + BONUS")
        assert len(errors) > 0

    def test_is_safe_valid(self, engine: FormulaEngine) -> None:
        assert engine.is_safe("SALARY * 2") is True

    def test_is_safe_invalid(self, engine: FormulaEngine) -> None:
        # A formula with random garbage should fail parsing → not safe
        assert engine.is_safe("import os") is False

    def test_check_variables_allowed(self, engine: FormulaEngine) -> None:
        unknown = engine.check_variables("SALARY + BONUS", {"SALARY", "BONUS"})
        assert unknown == []

    def test_check_variables_unknown(self, engine: FormulaEngine) -> None:
        unknown = engine.check_variables("SALARY + EVIL", {"SALARY"})
        assert "EVIL" in unknown


# ============================================================================
# Edge cases
# ============================================================================


class TestEdgeCases:
    def test_division_by_zero(self, engine: FormulaEngine) -> None:
        with pytest.raises(DivisionByZeroError):
            engine.evaluate("100 / 0", {})

    def test_division_by_zero_variable(self, engine: FormulaEngine) -> None:
        with pytest.raises(DivisionByZeroError):
            engine.evaluate("SALARY / DIVISOR", {"SALARY": 100, "DIVISOR": 0})

    def test_whitespace_handling(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("  2   +   3  ", {}) == Decimal("5")

    def test_large_numbers(self, engine: FormulaEngine) -> None:
        result = engine.evaluate("999999999 * 999999999", {})
        assert result == Decimal("999999998000000001")

    def test_zero_value(self, engine: FormulaEngine) -> None:
        assert engine.evaluate("0 * 1000000", {}) == Decimal("0")
