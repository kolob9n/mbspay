"""AttendanceType API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.attendance_types.schemas import (
    AttendanceTypeCreate,
    AttendanceTypeResponse,
    AttendanceTypeUpdate,
)
from app.modules.attendance_types.service import AttendanceTypeService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/attendance-types", tags=["Attendance Types"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AttendanceTypeService:
    return AttendanceTypeService(db)


@router.get("/", response_model=ApiResponse[list[AttendanceTypeResponse]])
async def list_types(
    service: Annotated[AttendanceTypeService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_all())


@router.post(
    "/seed",
    response_model=ApiResponse[list[AttendanceTypeResponse]],
    status_code=status.HTTP_201_CREATED,
)
async def seed_defaults(
    service: Annotated[AttendanceTypeService, Depends(get_service)],
):
    """Create default attendance types (WORK, WEEKEND, HOLIDAY, etc.). Idempotent."""
    return ApiResponse.ok(await service.seed_defaults())


@router.post(
    "/",
    response_model=ApiResponse[AttendanceTypeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_type(
    payload: AttendanceTypeCreate,
    service: Annotated[AttendanceTypeService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.patch("/{at_id}", response_model=ApiResponse[AttendanceTypeResponse])
async def update_type(
    at_id: UUID,
    payload: AttendanceTypeUpdate,
    service: Annotated[AttendanceTypeService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(at_id, payload))
