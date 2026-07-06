"""WorkSchedule API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.work_schedules.schemas import (
    WorkScheduleCreate,
    WorkScheduleResponse,
    WorkScheduleUpdate,
)
from app.modules.work_schedules.service import WorkScheduleService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/work-schedules", tags=["Work Schedules"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> WorkScheduleService:
    return WorkScheduleService(db)


@router.get("/", response_model=ApiResponse[list[WorkScheduleResponse]])
async def list_schedules(
    service: Annotated[WorkScheduleService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_all(page=page, size=size))


@router.get("/{ws_id}", response_model=ApiResponse[WorkScheduleResponse])
async def get_schedule(
    ws_id: UUID,
    service: Annotated[WorkScheduleService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_by_id(ws_id))


@router.post(
    "/",
    response_model=ApiResponse[WorkScheduleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    payload: WorkScheduleCreate,
    service: Annotated[WorkScheduleService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.patch("/{ws_id}", response_model=ApiResponse[WorkScheduleResponse])
async def update_schedule(
    ws_id: UUID,
    payload: WorkScheduleUpdate,
    service: Annotated[WorkScheduleService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(ws_id, payload))
