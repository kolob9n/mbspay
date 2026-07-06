"""Formula engine — AST node definitions."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Union


@dataclass
class NumberNode:
    value: Decimal


@dataclass
class VariableNode:
    name: str


@dataclass
class BinaryOpNode:
    op: str  # '+', '-', '*', '/'
    left: "ExprNode"
    right: "ExprNode"


@dataclass
class UnaryOpNode:
    op: str  # '-'
    operand: "ExprNode"


@dataclass
class FunctionNode:
    name: str  # 'MIN', 'MAX', 'ROUND', 'ABS', 'IF'
    args: list["ExprNode"] = field(default_factory=list)


# ---- Union type ------------------------------------------------------------
ExprNode = Union[NumberNode, VariableNode, BinaryOpNode, UnaryOpNode, FunctionNode]
