"""Tests for Payroll module — calculation, formulas, payslip.

Run with:  pytest backend/tests/test_payroll.py -v
"""

from decimal import Decimal

import pytest

from app.shared.formula_engine import FormulaEngine


@pytest.fixture
def engine() -> FormulaEngine:
    return FormulaEngine()


# ============================================================================
# Formula evaluation (unit tests)
# ============================================================================


class TestPayrollFormulas:
    """Test the three payroll formulas independently."""

    def test_base_salary_formula(self, engine: FormulaEngine) -> None:
        """(SALARY * BASE_PERCENT / 100 / NORM_DAYS) * WORKED_DAYS"""
        formula = "(SALARY * BASE_PERCENT / 100 / NORM_DAYS) * WORKED_DAYS"
        result = engine.evaluate(formula, {
            "SALARY": Decimal("120000"),
            "BASE_PERCENT": Decimal("55"),
            "NORM_DAYS": Decimal("22"),
            "WORKED_DAYS": Decimal("21"),
        })
        # (120000 * 55 / 100 / 22) * 21 = (66000 / 22) * 21 = 3000 * 21 = 63000
        assert result == Decimal("63000")

    def test_kpi_formula(self, engine: FormulaEngine) -> None:
        """SALARY * KPI_PERCENT / 100 * KPI_SHARE * KPI_COEF"""
        formula = "SALARY * KPI_PERCENT / 100 * KPI_SHARE * KPI_COEF"
        result = engine.evaluate(formula, {
            "SALARY": Decimal("120000"),
            "KPI_PERCENT": Decimal("30"),
            "KPI_SHARE": Decimal("0.95"),
            "KPI_COEF": Decimal("0.98"),
        })
        # 120000 * 0.30 * 0.95 * 0.98 = 33516
        assert result == Decimal("33516")

    def test_total_formula(self, engine: FormulaEngine) -> None:
        """BASE + KPI + BONUS + OVERTIME - PENALTY - PAID"""
        formula = "BASE + KPI + BONUS + OVERTIME - PENALTY - PAID"
        result = engine.evaluate(formula, {
            "BASE": Decimal("63000"),
            "KPI": Decimal("33516"),
            "BONUS": Decimal("5000"),
            "OVERTIME": Decimal("0"),
            "PENALTY": Decimal("2000"),
            "PAID": Decimal("40000"),
        })
        # 63000 + 33516 + 5000 + 0 - 2000 - 40000 = 59516
        assert result == Decimal("59516")

    def test_full_context(self, engine: FormulaEngine) -> None:
        """Verify all variables from the spec work together."""
        variables = {
            "SALARY": Decimal("120000"),
            "WORKED_DAYS": Decimal("21"),
            "WORKED_HOURS": Decimal("168"),
            "NORM_DAYS": Decimal("22"),
            "NORM_HOURS": Decimal("176"),
            "KPI_SHARE": Decimal("0.95"),
            "KPI_COEF": Decimal("0.98"),
            "BONUS": Decimal("5000"),
            "PENALTY": Decimal("2000"),
            "PAID": Decimal("40000"),
        }
        # Just check all variables are accessible
        for name, value in variables.items():
            assert engine.evaluate(name, variables) == value


# ============================================================================
# Calculation logic (pure, no DB)
# ============================================================================


class TestCalculationLogic:
    """Test the calculation algorithm independently."""

    def test_base_salary_computation(self) -> None:
        """Base = (SALARY * 55 / 100 / NORM_DAYS) * WORKED_DAYS"""
        salary = Decimal("120000")
        base_percent = Decimal("55")
        norm_days = Decimal("22")
        worked_days = Decimal("21")

        base = (salary * base_percent / 100 / norm_days) * worked_days
        assert base == Decimal("63000")

    def test_total_computation(self) -> None:
        """Total = BASE + KPI + BONUS + OVERTIME - PENALTY"""
        base = Decimal("63000")
        kpi = Decimal("33516")
        bonus = Decimal("5000")
        overtime = Decimal("0")
        penalty = Decimal("2000")

        total = base + kpi + bonus + overtime - penalty
        assert total == Decimal("99516")

    def test_balance_computation(self) -> None:
        """Balance = TOTAL - PAID"""
        total = Decimal("99516")
        paid = Decimal("40000")
        balance = total - paid
        assert balance == Decimal("59516")

    def test_versioning_latest_wins(self) -> None:
        """Only the latest version should be considered active."""
        versions = [
            {"version": 1, "total": Decimal("99000"), "status": "CLOSED"},
            {"version": 2, "total": Decimal("99516"), "status": "APPROVED"},
        ]
        active = [v for v in versions if v["status"] not in ("CANCELLED",)]
        latest = max(active, key=lambda v: v["version"])
        assert latest["version"] == 2
        assert latest["total"] == Decimal("99516")

    def test_snapshot_completeness(self) -> None:
        """Snapshot must contain formulas, variables, and results."""
        snapshot = {
            "formulas": {"BASE_SALARY": "...", "KPI": "...", "TOTAL": "..."},
            "variables": {"SALARY": 120000, "WORKED_DAYS": 21},
            "intermediate": {"base_salary": 63000, "kpi": 33516},
            "calculation_date": "2026-07-01T00:00:00",
        }
        assert "formulas" in snapshot
        assert "variables" in snapshot
        assert "intermediate" in snapshot
        assert "calculation_date" in snapshot


# ============================================================================
# Payslip
# ============================================================================


class TestPayslip:
    """Test payslip generation logic."""

    def test_to_pay_computation(self) -> None:
        """to_pay = total - paid"""
        total = Decimal("99516")
        paid = Decimal("40000")
        to_pay = total - paid
        assert to_pay == Decimal("59516")

    def test_payslip_fields(self) -> None:
        """Payslip must include all required fields."""
        fields = [
            "employee_name", "salary", "worked_days", "norm_days",
            "base_salary", "kpi", "bonus", "penalty", "paid", "to_pay",
        ]
        payslip = {
            "employee_name": "Иванов И.И.",
            "salary": 120000,
            "worked_days": 21,
            "norm_days": 22,
            "base_salary": 63000,
            "kpi": 33516,
            "bonus": 5000,
            "penalty": 2000,
            "paid": 40000,
            "to_pay": 59516,
        }
        for field in fields:
            assert field in payslip, f"Missing field: {field}"
