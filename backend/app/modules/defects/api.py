"""Defect API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.defects.schemas import (
    DefectCreate,
    DefectEmployeeSummary,
    DefectResponse,
    DefectTypeCreate,
    DefectTypeResponse,
    DefectTypeUpdate,
    DefectUpdate,
)
from app.modules.defects.service import DefectService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/defects", tags=["Defects"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DefectService:
    return DefectService(db)


# ---- Defect types ----------------------------------------------------------


@router.get("/types", response_model=ApiResponse[list[DefectTypeResponse]])
async def list_defect_types(
    service: Annotated[DefectService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_all_types())


@router.post(
    "/types",
    response_model=ApiResponse[DefectTypeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_defect_type(
    payload: DefectTypeCreate,
    service: Annotated[DefectService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create_type(payload))


@router.patch("/types/{dt_id}", response_model=ApiResponse[DefectTypeResponse])
async def update_defect_type(
    dt_id: UUID,
    payload: DefectTypeUpdate,
    service: Annotated[DefectService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update_type(dt_id, payload))


# ---- Defects ---------------------------------------------------------------


@router.get(
    "/employee/{employee_id}",
    response_model=ApiResponse[list[DefectResponse]],
)
async def get_employee_defects(
    employee_id: UUID,
    service: Annotated[DefectService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_by_employee(employee_id, page=page, size=size))


@router.post(
    "/",
    response_model=ApiResponse[DefectResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_defect(
    payload: DefectCreate,
    service: Annotated[DefectService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.patch("/{defect_id}", response_model=ApiResponse[DefectResponse])
async def update_defect(
    defect_id: UUID,
    payload: DefectUpdate,
    service: Annotated[DefectService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(defect_id, payload))
