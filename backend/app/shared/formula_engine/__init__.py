"""Formula Engine — safe mathematical expression interpreter.

This module is **standalone** — no dependencies on FastAPI, SQLAlchemy, or any
other application layer. It can be used from any service in the project.

Usage::

    from app.shared.formula_engine import FormulaEngine

    engine = FormulaEngine()
    result = engine.evaluate(
        formula="(SALARY * BASE_PERCENT / 100 / NORM_DAYS) * WORKED_DAYS",
        variables={"SALARY": 100000, "BASE_PERCENT": 55, "WORKED_DAYS": 20, "NORM_DAYS": 22},
    )
    print(result)  # Decimal('50000')

    engine.validate("SALARY + UNKNOWN")  # ["Неизвестная переменная: 'UNKNOWN'"]
    engine.get_variables("SALARY * 2 + BONUS")  # ["BONUS", "SALARY"]
"""

from decimal import Decimal

from app.shared.formula_engine.evaluator import evaluate_ast
from app.shared.formula_engine.exceptions import FormulaError
from app.shared.formula_engine.parser import parse_formula
from app.shared.formula_engine.validator import (
    check_variables,
    extract_variables,
    is_safe,
    validate_formula,
)


class FormulaEngine:
    """Public API for the formula engine.

    Completely standalone — no database, no HTTP, no external dependencies.
    """

    def evaluate(
        self,
        formula: str,
        variables: dict[str, int | float | Decimal],
    ) -> Decimal:
        """Parse and evaluate a formula with the given variable values.

        Args:
            formula: The expression string, e.g. ``"SALARY * 2 + BONUS"``.
            variables: Dict mapping variable names to numeric values.

        Returns:
            The computed result as ``Decimal``.

        Raises:
            FormulaSyntaxError: Invalid syntax.
            UnknownVariableError: Variable referenced in formula but not provided.
            DivisionByZeroError: Division by zero detected.
        """
        # Convert all values to Decimal for precision
        dec_vars = {k: Decimal(str(v)) for k, v in variables.items()}
        ast = parse_formula(formula)
        return evaluate_ast(ast, dec_vars)

    def validate(self, formula: str) -> list[str]:
        """Check formula syntax. Returns list of errors (empty = valid)."""
        return validate_formula(formula)

    def get_variables(self, formula: str) -> list[str]:
        """Extract all variable names referenced in the formula."""
        return extract_variables(formula)

    def check_variables(
        self, formula: str, allowed: set[str] | None = None
    ) -> list[str]:
        """Return variables in formula that are NOT in the allowed set."""
        return check_variables(formula, allowed)

    def is_safe(self, formula: str) -> bool:
        """Check that the formula contains no forbidden constructs."""
        return is_safe(formula)


# Singleton instance for convenience
engine = FormulaEngine()
