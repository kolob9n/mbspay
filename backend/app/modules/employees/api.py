"""Employee API — HTTP layer.

Thin layer: receives request → calls Service → wraps in ApiResponse.
No business logic, no SQLAlchemy.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.employees.schemas import (
    EmployeeCardResponse,
    EmployeeCreate,
    EmployeeDismiss,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.modules.employees.service import EmployeeService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/employees", tags=["Employees"])


# ---- Dependency ------------------------------------------------------------
def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> EmployeeService:
    return EmployeeService(db)


# ---- Routes ----------------------------------------------------------------

@router.get("/", response_model=ApiResponse[list[EmployeeCardResponse]])
async def list_employees(
    service: Annotated[EmployeeService, Depends(get_service)],
    is_active: Annotated[Optional[bool], Query()] = None,
    department_id: Annotated[Optional[UUID], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List employees with optional filters."""
    return ApiResponse.ok(
        await service.get_all_employees(
            is_active=is_active, department_id=department_id, page=page, size=size
        )
    )


@router.get("/active", response_model=ApiResponse[list[EmployeeCardResponse]])
async def list_active_employees(
    service: Annotated[EmployeeService, Depends(get_service)],
    department_id: Annotated[Optional[UUID], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List only active employees."""
    return ApiResponse.ok(
        await service.get_active_employees(
            department_id=department_id, page=page, size=size
        )
    )


@router.get("/{emp_id}", response_model=ApiResponse[EmployeeCardResponse])
async def get_employee(
    emp_id: UUID,
    service: Annotated[EmployeeService, Depends(get_service)],
):
    """Get full employee card by ID."""
    return ApiResponse.ok(await service.get_employee_card(emp_id))


@router.post(
    "/",
    response_model=ApiResponse[EmployeeCardResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    payload: EmployeeCreate,
    service: Annotated[EmployeeService, Depends(get_service)],
):
    """Hire a new employee."""
    return ApiResponse.ok(await service.hire_employee(payload))


@router.patch("/{emp_id}", response_model=ApiResponse[EmployeeCardResponse])
async def update_employee(
    emp_id: UUID,
    payload: EmployeeUpdate,
    service: Annotated[EmployeeService, Depends(get_service)],
):
    """Update employee data (employee_number cannot be changed)."""
    return ApiResponse.ok(await service.update_employee(emp_id, payload))


@router.post("/{emp_id}/dismiss", response_model=ApiResponse[EmployeeCardResponse])
async def dismiss_employee(
    emp_id: UUID,
    payload: EmployeeDismiss,
    service: Annotated[EmployeeService, Depends(get_service)],
):
    """Dismiss an employee (soft-deactivate)."""
    return ApiResponse.ok(await service.dismiss_employee(emp_id, payload))
