"""Formula service — wraps the standalone FormulaEngine with CRUD operations."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.formula_engine.repository import FormulaRepository
from app.modules.formula_engine.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    FormulaCreate,
    FormulaResponse,
    FormulaUpdate,
    ValidateRequest,
    ValidateResponse,
)
from app.shared.exceptions import BusinessRuleException, ConflictException, NotFoundException
from app.shared.formula_engine import FormulaEngine, FormulaError


class FormulaService:
    """CRUD + evaluate/validate service for stored formulas."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = FormulaRepository(session)
        self._engine = FormulaEngine()

    # ---- CRUD --------------------------------------------------------------

    async def create(self, payload: FormulaCreate) -> FormulaResponse:
        # Validate expression before saving
        errors = self._engine.validate(payload.expression)
        if errors:
            raise BusinessRuleException(
                f"Некорректная формула: {'; '.join(errors)}"
            )

        existing = await self._repo.get_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Формула с кодом '{payload.code}' уже существует.")

        f = await self._repo.create(**payload.model_dump())
        return FormulaResponse.model_validate(f)

    async def get_all(self, *, page: int = 1, size: int = 100) -> list[FormulaResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(offset=offset, limit=size)
        return [FormulaResponse.model_validate(f) for f in items]

    async def get_by_id(self, formula_id: UUID) -> FormulaResponse:
        f = await self._repo.get_by_id(formula_id)
        if f is None:
            raise NotFoundException(f"Формула с id={formula_id} не найдена.")
        return FormulaResponse.model_validate(f)

    async def update(self, formula_id: UUID, payload: FormulaUpdate) -> FormulaResponse:
        f = await self._repo.get_by_id(formula_id)
        if f is None:
            raise NotFoundException(f"Формула с id={formula_id} не найдена.")

        if payload.expression is not None:
            errors = self._engine.validate(payload.expression)
            if errors:
                raise BusinessRuleException(
                    f"Некорректная формула: {'; '.join(errors)}"
                )

        updated = await self._repo.update(f, **payload.model_dump(exclude_none=True))
        return FormulaResponse.model_validate(updated)

    # ---- Engine wrappers ---------------------------------------------------

    async def evaluate(self, payload: EvaluateRequest) -> EvaluateResponse:
        """Evaluate a formula (inline or stored) with given variables."""
        try:
            result = self._engine.evaluate(payload.formula, payload.variables)
        except FormulaError as e:
            raise BusinessRuleException(str(e))
        return EvaluateResponse(result=result)

    async def validate_formula(self, payload: ValidateRequest) -> ValidateResponse:
        """Validate a formula and return its variables."""
        errors = self._engine.validate(payload.formula)
        variables: list[str] = []
        if not errors:
            try:
                variables = self._engine.get_variables(payload.formula)
            except FormulaError:
                pass
        return ValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            variables=variables,
        )
