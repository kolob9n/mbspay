"""Security API — HTTP layer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.security.schemas import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    PermissionCreate,
    PermissionResponse,
    RefreshRequest,
    RefreshResponse,
    RoleCreate,
    RoleResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.modules.security.service import SecurityService
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/security", tags=["Security"])


def get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> SecurityService:
    return SecurityService(db)


# ---- Auth ------------------------------------------------------------------


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(
    payload: LoginRequest,
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.login(payload))


@router.post("/refresh", response_model=ApiResponse[RefreshResponse])
async def refresh(
    payload: RefreshRequest,
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.refresh(payload))


@router.get("/me", response_model=ApiResponse[MeResponse])
async def get_me(
    service: Annotated[SecurityService, Depends(get_service)],
):
    # Stub — in production, user_id from JWT
    from uuid import uuid4
    return ApiResponse.ok(await service.get_me(uuid4()))


# ---- Users -----------------------------------------------------------------


@router.get("/users", response_model=ApiResponse[list[UserResponse]])
async def list_users(
    service: Annotated[SecurityService, Depends(get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return ApiResponse.ok(await service.get_users(page=page, size=size))


@router.post(
    "/users",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreate,
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create_user(payload))


@router.patch("/users/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.update_user(user_id, payload))


# ---- Roles -----------------------------------------------------------------


@router.get("/roles", response_model=ApiResponse[list[RoleResponse]])
async def list_roles(
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_roles())


@router.post(
    "/roles",
    response_model=ApiResponse[RoleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    payload: RoleCreate,
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create_role(payload))


@router.post("/roles/seed", response_model=ApiResponse[list[RoleResponse]])
async def seed_roles(
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.seed_default_roles())


# ---- Permissions -----------------------------------------------------------


@router.get("/permissions", response_model=ApiResponse[list[PermissionResponse]])
async def list_permissions(
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.get_permissions())


@router.post(
    "/permissions",
    response_model=ApiResponse[PermissionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    payload: PermissionCreate,
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.create_permission(payload))


@router.post(
    "/permissions/seed",
    response_model=ApiResponse[list[PermissionResponse]],
)
async def seed_permissions(
    service: Annotated[SecurityService, Depends(get_service)],
):
    return ApiResponse.ok(await service.seed_default_permissions())
