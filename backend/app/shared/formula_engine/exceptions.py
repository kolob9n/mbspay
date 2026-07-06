"""Formula engine — typed exceptions."""


class FormulaError(Exception):
    """Base exception for all formula-related errors."""
    pass


class FormulaSyntaxError(FormulaError):
    """Invalid formula syntax."""
    def __init__(self, message: str, position: int | None = None) -> None:
        self.position = position
        detail = f"Синтаксическая ошибка: {message}"
        if position is not None:
            detail += f" (позиция {position})"
        super().__init__(detail)


class UnknownVariableError(FormulaError):
    """Reference to an unknown variable."""
    def __init__(self, variable_name: str) -> None:
        self.variable_name = variable_name
        super().__init__(f"Неизвестная переменная: '{variable_name}'")


class DivisionByZeroError(FormulaError):
    """Attempted division by zero."""
    def __init__(self) -> None:
        super().__init__("Деление на ноль")


class EvaluationError(FormulaError):
    """Generic evaluation error."""
    pass


class ForbiddenConstructError(FormulaError):
    """Forbidden construct detected in formula."""
    def __init__(self, detail: str = "Запрещённая конструкция") -> None:
        super().__init__(detail)
