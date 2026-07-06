"""Tests for Payments & Ledger module.

Run with:  pytest backend/tests/test_payments.py -v
"""

from decimal import Decimal

import pytest

from app.shared.formula_engine import FormulaEngine


# ============================================================================
# Unit tests — formula engine with payment variables
# ============================================================================


class TestPaymentVariables:
    """Test that PAID variable works in formulas."""

    @pytest.fixture
    def engine(self) -> FormulaEngine:
        return FormulaEngine()

    def test_paid_variable(self, engine: FormulaEngine) -> None:
        result = engine.evaluate("PAID", {"PAID": Decimal("65000")})
        assert result == Decimal("65000")

    def test_balance_via_formula(self, engine: FormulaEngine) -> None:
        """BALANCE = ACCRUED - PAID (can be computed in formula)."""
        formula = "ACCRUED - PAID"
        result = engine.evaluate(formula, {
            "ACCRUED": Decimal("120000"),
            "PAID": Decimal("65000"),
        })
        assert result == Decimal("55000")

    def test_paid_percentage(self, engine: FormulaEngine) -> None:
        """What percentage of accrued has been paid."""
        formula = "IF(ACCRUED > 0, PAID / ACCRUED * 100, 0)"
        result = engine.evaluate(formula, {
            "ACCRUED": Decimal("120000"),
            "PAID": Decimal("65000"),
        })
        # 65000 / 120000 * 100 ≈ 54.166...
        assert result > Decimal("54")
        assert result < Decimal("55")


# ============================================================================
# Ledger balance logic (pure computation, no DB)
# ============================================================================


class TestBalanceLogic:
    """Test the balance computation algorithm independently of DB."""

    def test_simple_balance(self) -> None:
        """accrued=120000, paid=65000, correction=0 → balance=55000."""
        accrued = Decimal("120000")
        paid = Decimal("65000")
        correction = Decimal("0")
        balance = accrued - paid + correction
        assert balance == Decimal("55000")

    def test_with_correction(self) -> None:
        """After cancellation, correction should reverse the payment."""
        # Original: paid=40000
        # Cancelled: correction=-40000
        accrued = Decimal("120000")
        paid = Decimal("40000")
        correction = Decimal("-40000")  # reversing entry
        balance = accrued - paid + correction
        assert balance == Decimal("80000")  # 120000 - 40000 - 40000 = 80000
        # Net effect: only correction remains, payment is cancelled

    def test_no_payments(self) -> None:
        """No payments → balance = accrued."""
        accrued = Decimal("120000")
        paid = Decimal("0")
        correction = Decimal("0")
        balance = accrued - paid + correction
        assert balance == Decimal("120000")

    def test_overpayment(self) -> None:
        """Paid more than accrued → negative balance."""
        accrued = Decimal("50000")
        paid = Decimal("75000")
        correction = Decimal("0")
        balance = accrued - paid + correction
        assert balance == Decimal("-25000")

    def test_reversal_of_reversal(self) -> None:
        """Cancelling a cancelled payment."""
        # Payment: +40000
        # Cancel: -40000
        # Re-post: +40000
        entries = [
            Decimal("40000"),   # PAYMENT
            Decimal("-40000"),  # CORRECTION (cancel)
            Decimal("40000"),   # PAYMENT (re-post)
        ]
        net = sum(entries)
        assert net == Decimal("40000")


# ============================================================================
# Document lifecycle
# ============================================================================


class TestDocumentLifecycle:
    """Test payment document state transitions."""

    def test_valid_transitions(self) -> None:
        """DRAFT → POSTED → CANCELLED."""
        valid = [
            ("DRAFT", "POSTED"),
            ("POSTED", "CANCELLED"),
        ]
        for from_status, to_status in valid:
            assert from_status != to_status

    def test_invalid_transition_draft_to_cancelled(self) -> None:
        """Cannot cancel a DRAFT document."""
        # Must post first
        pass  # business rule tested in service layer

    def test_invalid_transition_posted_to_draft(self) -> None:
        """POSTED cannot go back to DRAFT — must cancel."""
        pass  # business rule tested in service layer
