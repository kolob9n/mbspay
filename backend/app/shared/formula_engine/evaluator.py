"""Formula engine — AST evaluator.

Walks the AST and computes the result using provided variable values.
Completely safe — no eval(), no code execution from strings.
"""

from decimal import Decimal

from app.shared.formula_engine.ast_nodes import (
    BinaryOpNode,
    ExprNode,
    FunctionNode,
    NumberNode,
    UnaryOpNode,
    VariableNode,
)
from app.shared.formula_engine.exceptions import (
    DivisionByZeroError,
    EvaluationError,
    UnknownVariableError,
)
from app.shared.formula_engine.functions import FUNCTION_REGISTRY


class Evaluator:
    """Walks an AST and computes the numeric result."""

    def __init__(self, variables: dict[str, Decimal]) -> None:
        self._vars = variables

    def evaluate(self, node: ExprNode) -> Decimal:
        """Evaluate an AST node recursively."""
        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, VariableNode):
            if node.name not in self._vars:
                raise UnknownVariableError(node.name)
            return self._vars[node.name]

        if isinstance(node, UnaryOpNode):
            operand = self.evaluate(node.operand)
            if node.op == "-":
                return -operand
            raise EvaluationError(f"Неизвестный унарный оператор: {node.op}")

        if isinstance(node, BinaryOpNode):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            if node.op == "+":
                return left + right
            if node.op == "-":
                return left - right
            if node.op == "*":
                return left * right
            if node.op == "/":
                if right == 0:
                    raise DivisionByZeroError()
                return left / right
            raise EvaluationError(f"Неизвестный оператор: {node.op}")

        if isinstance(node, FunctionNode):
            func = FUNCTION_REGISTRY.get(node.name)
            if func is None:
                raise EvaluationError(f"Неизвестная функция: {node.name}")
            args = [self.evaluate(a) for a in node.args]
            return func(*args)

        raise EvaluationError(f"Неизвестный тип узла: {type(node).__name__}")


def evaluate_ast(node: ExprNode, variables: dict[str, Decimal]) -> Decimal:
    """Convenience: evaluate an AST with given variables."""
    return Evaluator(variables).evaluate(node)
