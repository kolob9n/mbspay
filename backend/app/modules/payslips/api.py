"""Payslip API — HTTP layer."""

from io import BytesIO
from typing import Annotated, Optional
from uuid import UUID
from zipfile import ZipFile

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.payslips.models import PayslipStatus
from app.modules.payslips.schemas import (
    PayslipDetailResponse,
    PayslipResponse,
)
from app.modules.payslips.service import PayslipService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/payslips", tags=["Payslips"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PayslipService:
    return PayslipService(db)


# ---- CRUD ------------------------------------------------------------------


@router.get("/", response_model=ApiResponse[list[PayslipResponse]])
async def list_payslips(
    service: Annotated[PayslipService, Depends(get_service)],
    period_id: Annotated[Optional[UUID], Query()] = None,
    employee_id: Annotated[Optional[UUID], Query()] = None,
    status_filter: Annotated[Optional[PayslipStatus], Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return ApiResponse.ok(await service.get_all(
        period_id=period_id, employee_id=employee_id, status=status_filter, page=page, size=size,
    ))


@router.get("/{ps_id}", response_model=ApiResponse[PayslipDetailResponse])
async def get_payslip(
    ps_id: UUID,
    service: Annotated[PayslipService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_by_id(ps_id))


@router.get("/employee/{employee_id}", response_model=ApiResponse[list[PayslipResponse]])
async def get_employee_payslips(
    employee_id: UUID,
    service: Annotated[PayslipService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_by_employee(employee_id, page=page, size=size))


# ---- Generation ------------------------------------------------------------


@router.post("/generate/{payroll_run_id}", response_model=ApiResponse[list[PayslipResponse]])
async def generate_all(
    payroll_run_id: UUID,
    service: Annotated[PayslipService, Depends(get_service)],
):
    return ApiResponse.ok(await service.generate_all(payroll_run_id))


# ---- PDF / Download --------------------------------------------------------


@router.get("/{ps_id}/pdf", response_class=Response)
async def get_pdf(
    ps_id: UUID,
    service: Annotated[PayslipService, Depends(get_service)],
):
    html = await service.generate_html(ps_id)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/download/{payroll_run_id}")
async def download_zip(
    payroll_run_id: UUID,
    service: Annotated[PayslipService, Depends(get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payslips = await service.get_all(period_id=None, size=10000)
    zip_buf = BytesIO()
    with ZipFile(zip_buf, "w") as zf:
        for ps in payslips:
            html = await service.generate_html(ps.id)
            zf.writestr(f"payslip_{ps.number}.html", html)
    zip_buf.seek(0)
    return StreamingResponse(
        zip_buf, media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=payslips.zip"},
    )
