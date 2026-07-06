"""Security Pydantic schemas (v2)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Auth ------------------------------------------------------------------


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


# ---- User ------------------------------------------------------------------


class UserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str | None = None
    employee_id: UUID | None = None
    role_id: UUID


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    email: str | None = None
    is_active: bool | None = None
    role_id: UUID | None = None


class UserResponse(BaseModel):
    id: UUID
    login: str
    full_name: str
    email: Optional[str] = None
    employee_id: Optional[UUID] = None
    is_active: bool
    role_id: UUID
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Role ------------------------------------------------------------------


class RoleCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    permission_ids: list[UUID] = []


class RoleResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    permissions: list["PermissionResponse"] = []

    model_config = {"from_attributes": True}


# ---- Permission ------------------------------------------------------------


class PermissionCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    module: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)


class PermissionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    module: str
    action: str

    model_config = {"from_attributes": True}


# ---- Me --------------------------------------------------------------------


class MeResponse(BaseModel):
    user: UserResponse
    role: RoleResponse
    permissions: list[str] = []
