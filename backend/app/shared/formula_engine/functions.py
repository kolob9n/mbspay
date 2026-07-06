"""Formula engine — built-in function registry."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Callable

from app.shared.formula_engine.exceptions import EvaluationError

# ---- Type alias ------------------------------------------------------------
FuncImpl = Callable[..., Decimal]


def _fn_min(*args: Decimal) -> Decimal:
    if not args:
        raise EvaluationError("MIN() требует хотя бы один аргумент.")
    return min(args)


def _fn_max(*args: Decimal) -> Decimal:
    if not args:
        raise EvaluationError("MAX() требует хотя бы один аргумент.")
    return max(args)


def _fn_round(*args: Decimal) -> Decimal:
    if len(args) != 1:
        raise EvaluationError("ROUND() принимает ровно один аргумент.")
    return args[0].quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _fn_abs(*args: Decimal) -> Decimal:
    if len(args) != 1:
        raise EvaluationError("ABS() принимает ровно один аргумент.")
    return abs(args[0])


def _fn_if(*args: Decimal) -> Decimal:
    if len(args) != 3:
        raise EvaluationError("IF() принимает ровно три аргумента: условие, значение_если_истина, значение_если_ложь.")
    condition = args[0]
    return args[1] if condition != 0 else args[2]


# ---- Registry --------------------------------------------------------------
FUNCTION_REGISTRY: dict[str, FuncImpl] = {
    "MIN": _fn_min,
    "MAX": _fn_max,
    "ROUND": _fn_round,
    "ABS": _fn_abs,
    "IF": _fn_if,
}
