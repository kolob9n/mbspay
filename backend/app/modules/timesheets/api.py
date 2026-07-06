"""Timesheet API — HTTP layer.

Thin layer: receives request → calls Service → wraps in ApiResponse.
No business logic, no SQLAlchemy.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.timesheets.models import TimesheetStatus
from app.modules.timesheets.schemas import (
    TimesheetCreate,
    TimesheetDetailResponse,
    TimesheetEntryResponse,
    TimesheetEntryUpdate,
    TimesheetMatrixResponse,
    TimesheetResponse,
    TimesheetSummaryResponse,
)
from app.modules.timesheets.service import TimesheetService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/timesheets", tags=["Timesheets"])


# ---- Dependency ------------------------------------------------------------
def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TimesheetService:
    return TimesheetService(db)


# ---- Timesheet routes ------------------------------------------------------

@router.get("/", response_model=ApiResponse[list[TimesheetResponse]])
async def list_timesheets(
    service: Annotated[TimesheetService, Depends(get_service)],
    department_id: Annotated[Optional[UUID], Query()] = None,
    status: Annotated[Optional[TimesheetStatus], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List timesheets with optional department/status filters."""
    return ApiResponse.ok(
        await service.get_all(
            department_id=department_id, status=status, page=page, size=size
        )
    )


@router.post(
    "/",
    response_model=ApiResponse[TimesheetDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_timesheet(
    payload: TimesheetCreate,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Create timesheet + auto-fill entries from calendar and employees."""
    return ApiResponse.ok(await service.create_timesheet(payload))


@router.get("/{ts_id}", response_model=ApiResponse[TimesheetDetailResponse])
async def get_timesheet(
    ts_id: UUID,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Get timesheet with all entries."""
    return ApiResponse.ok(await service.get_timesheet(ts_id))


# ---- Matrix view -----------------------------------------------------------

@router.get("/{ts_id}/matrix", response_model=ApiResponse[TimesheetMatrixResponse])
async def get_matrix(
    ts_id: UUID,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Get timesheet as employee × day matrix for frontend table view."""
    return ApiResponse.ok(await service.get_matrix(ts_id))


# ---- Summary ---------------------------------------------------------------

@router.get(
    "/{ts_id}/summary", response_model=ApiResponse[TimesheetSummaryResponse]
)
async def get_summary(
    ts_id: UUID,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Get aggregated summary: worked days, hours, vacation, sick, overtime."""
    return ApiResponse.ok(await service.calculate_summary(ts_id))


# ---- Entry routes ----------------------------------------------------------

@router.patch(
    "/entry/{entry_id}", response_model=ApiResponse[TimesheetEntryResponse]
)
async def update_entry(
    entry_id: UUID,
    payload: TimesheetEntryUpdate,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Update a single timesheet entry (type, hours, comment).

    Blocked after SUBMITTED/APPROVED/CLOSED.
    """
    return ApiResponse.ok(await service.update_entry(entry_id, payload))


# ---- Workflow routes -------------------------------------------------------

@router.post("/{ts_id}/submit", response_model=ApiResponse[TimesheetResponse])
async def submit(
    ts_id: UUID,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Submit timesheet for approval (DRAFT/RETURNED → SUBMITTED)."""
    return ApiResponse.ok(await service.submit(ts_id))


@router.post("/{ts_id}/approve", response_model=ApiResponse[TimesheetResponse])
async def approve(
    ts_id: UUID,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Approve timesheet (SUBMITTED → APPROVED)."""
    # In production, approved_by comes from JWT
    return ApiResponse.ok(
        await service.approve(ts_id, approved_by=UUID("00000000-0000-0000-0000-000000000000"))
    )


@router.post("/{ts_id}/return", response_model=ApiResponse[TimesheetResponse])
async def return_to_revision(
    ts_id: UUID,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Return timesheet for revision (SUBMITTED → RETURNED)."""
    return ApiResponse.ok(await service.return_to_revision(ts_id))


@router.post("/{ts_id}/close", response_model=ApiResponse[TimesheetResponse])
async def close_timesheet(
    ts_id: UUID,
    service: Annotated[TimesheetService, Depends(get_service)],
):
    """Close timesheet (APPROVED → CLOSED). No further edits allowed."""
    return ApiResponse.ok(await service.close(ts_id))
