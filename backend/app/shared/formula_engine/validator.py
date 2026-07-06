"""Formula engine — validation and variable extraction."""

from decimal import Decimal

from app.shared.formula_engine.ast_nodes import (
    BinaryOpNode,
    ExprNode,
    FunctionNode,
    NumberNode,
    VariableNode,
)
from app.shared.formula_engine.exceptions import (
    FormulaError,
    FormulaSyntaxError,
)
from app.shared.formula_engine.parser import Parser, parse_formula


def validate_formula(source: str) -> list[str]:
    """Validate formula syntax and return list of syntax issues (empty = valid).

    Returns a list of error messages. Empty list means the formula is valid.
    """
    errors: list[str] = []
    try:
        parse_formula(source)
    except FormulaSyntaxError as e:
        errors.append(str(e))
    return errors


def extract_variables(source: str) -> list[str]:
    """Parse the formula and return the sorted list of variable names used."""
    ast = parse_formula(source)
    variables: set[str] = set()

    def walk(node: ExprNode) -> None:
        if isinstance(node, VariableNode):
            variables.add(node.name)
        elif isinstance(node, BinaryOpNode):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, FunctionNode):
            for arg in node.args:
                walk(arg)

    walk(ast)
    return sorted(variables)


def check_variables(
    source: str, allowed_variables: set[str] | None = None
) -> list[str]:
    """Return list of unknown variables in the formula.

    If allowed_variables is None, all variables are considered valid.
    """
    try:
        used = extract_variables(source)
    except FormulaError:
        return []
    if allowed_variables is None:
        return []
    return [v for v in used if v not in allowed_variables]


def is_safe(source: str) -> bool:
    """Check that the formula contains no forbidden constructs."""
    # The parser itself is the safety check — if it can't parse it, it's rejected.
    try:
        parse_formula(source)
        return True
    except FormulaError:
        return False
