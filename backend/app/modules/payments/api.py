"""Payment API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.payments.models import PaymentStatus
from app.modules.payments.schemas import (
    PaymentCreate,
    PaymentDetailResponse,
    PaymentImportResult,
    PaymentResponse,
    PaymentUpdate,
)
from app.modules.payments.service import PaymentService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PaymentService:
    return PaymentService(db)


# ---- CRUD ------------------------------------------------------------------


@router.get("/", response_model=ApiResponse[list[PaymentResponse]])
async def list_payments(
    service: Annotated[PaymentService, Depends(get_service)],
    status_filter: Annotated[PaymentStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return ApiResponse.ok(await service.get_all(status=status_filter, page=page, size=size))


@router.post(
    "/",
    response_model=ApiResponse[PaymentDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payload: PaymentCreate,
    service: Annotated[PaymentService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create(payload))


@router.get("/{payment_id}", response_model=ApiResponse[PaymentDetailResponse])
async def get_payment(
    payment_id: UUID,
    service: Annotated[PaymentService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_by_id(payment_id))


@router.patch("/{payment_id}", response_model=ApiResponse[PaymentDetailResponse])
async def update_payment(
    payment_id: UUID,
    payload: PaymentUpdate,
    service: Annotated[PaymentService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update(payment_id, payload))


# ---- Workflow --------------------------------------------------------------


@router.post("/{payment_id}/post", response_model=ApiResponse[PaymentDetailResponse])
async def post_payment(
    payment_id: UUID,
    service: Annotated[PaymentService, Depends(get_service)],
):
    """Post payment → creates ledger entries."""
    return ApiResponse.ok(await service.post(payment_id))


@router.post("/{payment_id}/cancel", response_model=ApiResponse[PaymentDetailResponse])
async def cancel_payment(
    payment_id: UUID,
    service: Annotated[PaymentService, Depends(get_service)],
):
    """Cancel payment → creates reversing ledger entries."""
    return ApiResponse.ok(await service.cancel(payment_id))


# ---- Import ----------------------------------------------------------------


@router.post("/import", response_model=ApiResponse[PaymentImportResult])
async def import_payments(
    file: Annotated[UploadFile, File(...)],
    payroll_period_id: UUID = Query(...),
    service: Annotated[PaymentService, Depends(get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Import payments from Excel (.xlsx)."""
    from app.shared.services.payment_import_service import PaymentImportService

    import_service = PaymentImportService(db)
    result = await import_service.import_file(
        file=file,
        payroll_period_id=payroll_period_id,
    )
    return ApiResponse.ok(result)
