"""Settings API — HTTP layer."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.settings.schemas import (
    SettingCreate,
    SettingResponse,
    SettingUpdate,
)
from app.modules.settings.service import SettingsService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/settings", tags=["Settings"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> SettingsService:
    return SettingsService(db)


@router.get("/", response_model=ApiResponse[list[SettingResponse]])
async def list_settings(
    service: Annotated[SettingsService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_all())


@router.post("/seed", response_model=ApiResponse[list[SettingResponse]])
async def seed_settings(
    service: Annotated[SettingsService, Depends(get_service)],
):
    return ApiResponse.ok(await service.seed_defaults())


@router.post(
    "/",
    response_model=ApiResponse[SettingResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_setting(
    payload: SettingCreate,
    service: Annotated[SettingsService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.patch("/{key}", response_model=ApiResponse[SettingResponse])
async def update_setting(
    key: str,
    payload: SettingUpdate,
    service: Annotated[SettingsService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(key, payload))
