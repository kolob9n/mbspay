"""Department API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.departments.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.modules.departments.service import DepartmentService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DepartmentService:
    return DepartmentService(db)


@router.get("/", response_model=ApiResponse[list[DepartmentResponse]])
async def list_departments(
    service: Annotated[DepartmentService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_all(page=page, size=size))


@router.get("/{dept_id}", response_model=ApiResponse[DepartmentResponse])
async def get_department(
    dept_id: UUID,
    service: Annotated[DepartmentService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_by_id(dept_id))


@router.post(
    "/", response_model=ApiResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED
)
async def create_department(
    payload: DepartmentCreate,
    service: Annotated[DepartmentService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.patch("/{dept_id}", response_model=ApiResponse[DepartmentResponse])
async def update_department(
    dept_id: UUID,
    payload: DepartmentUpdate,
    service: Annotated[DepartmentService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(dept_id, payload))
