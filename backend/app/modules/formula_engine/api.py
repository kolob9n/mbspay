"""Formula Engine API — HTTP layer.

Thin layer: receives request → calls Service → wraps in ApiResponse.
No business logic, no SQLAlchemy.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.formula_engine.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    FormulaCreate,
    FormulaResponse,
    FormulaUpdate,
    ValidateRequest,
    ValidateResponse,
)
from app.modules.formula_engine.service import FormulaService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/formulas", tags=["Formula Engine"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> FormulaService:
    return FormulaService(db)


# ---- Formula CRUD ----------------------------------------------------------

@router.get("/", response_model=ApiResponse[list[FormulaResponse]])
async def list_formulas(
    service: Annotated[FormulaService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_all(page=page, size=size))


@router.post(
    "/",
    response_model=ApiResponse[FormulaResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_formula(
    payload: FormulaCreate,
    service: Annotated[FormulaService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.patch("/{formula_id}", response_model=ApiResponse[FormulaResponse])
async def update_formula(
    formula_id: UUID,
    payload: FormulaUpdate,
    service: Annotated[FormulaService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(formula_id, payload))


# ---- Engine operations -----------------------------------------------------

@router.post("/validate", response_model=ApiResponse[ValidateResponse])
async def validate_formula(
    payload: ValidateRequest,
    service: Annotated[FormulaService, Depends(get_service)],
):
    """Validate formula syntax and extract variables."""
    return ApiResponse.ok(await service.validate_formula(payload))


@router.post("/evaluate", response_model=ApiResponse[EvaluateResponse])
async def evaluate_formula(
    payload: EvaluateRequest,
    service: Annotated[FormulaService, Depends(get_service)],
):
    """Safely evaluate a formula with given variable values.

    Supports: +, -, *, /, (), MIN, MAX, ROUND, ABS, IF.
    No eval() — fully interpreted AST.
    """
    return ApiResponse.ok(await service.evaluate(payload))
