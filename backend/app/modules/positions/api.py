"""Position API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.positions.schemas import (
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)
from app.modules.positions.service import PositionService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/positions", tags=["Positions"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PositionService:
    return PositionService(db)


@router.get("/", response_model=ApiResponse[list[PositionResponse]])
async def list_positions(
    service: Annotated[PositionService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_all(page=page, size=size))


@router.get("/{pos_id}", response_model=ApiResponse[PositionResponse])
async def get_position(
    pos_id: UUID,
    service: Annotated[PositionService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_by_id(pos_id))


@router.post(
    "/", response_model=ApiResponse[PositionResponse], status_code=status.HTTP_201_CREATED
)
async def create_position(
    payload: PositionCreate,
    service: Annotated[PositionService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.patch("/{pos_id}", response_model=ApiResponse[PositionResponse])
async def update_position(
    pos_id: UUID,
    payload: PositionUpdate,
    service: Annotated[PositionService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(pos_id, payload))
