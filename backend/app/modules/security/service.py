"""Security service — auth, users, roles, permissions."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
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
from app.shared.exceptions import (
    AppException,
    BusinessRuleException,
    ConflictException,
    NotFoundException,
)


class SecurityService:
    """Authentication, authorization, user/role/permission management."""

    def __init__(self, session: AsyncSession) -> None:
        from app.modules.security.repository import SecurityRepository
        self._repo = SecurityRepository(session)

    # ========================================================================
    # Auth
    # ========================================================================

    async def login(self, payload: LoginRequest) -> LoginResponse:
        # DEV bypass: no database needed when DEBUG=True
        if settings.DEBUG and payload.login == "admin" and payload.password == "admin":
            return LoginResponse(
                access_token=create_access_token("dev-admin", "admin"),
                refresh_token="dev-refresh-token",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

        user = await self._repo.get_user_by_login(payload.login)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise AppException("Неверный логин или пароль")

        if not user.is_active:
            raise BusinessRuleException("Учётная запись заблокирована")

        # Update last_login
        user.last_login = datetime.now(timezone.utc)

        # Generate tokens
        access_token = create_access_token(user.id, user.login)
        refresh_token_str = uuid.uuid4().hex + uuid.uuid4().hex

        # Save refresh token
        from app.modules.security.models import RefreshToken
        await self._repo.save_refresh_token(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, payload: RefreshRequest) -> RefreshResponse:
        rt = await self._repo.get_refresh_token(payload.refresh_token)
        if rt is None or rt.revoked:
            raise AppException("Недействительный refresh-токен")
        if rt.expires_at < datetime.now(timezone.utc):
            raise AppException("Срок действия refresh-токена истёк")

        # Revoke old
        rt.revoked = True

        user = await self._repo.get_user_by_id(rt.user_id)
        if user is None or not user.is_active:
            raise AppException("Пользователь не найден или заблокирован")

        # Issue new pair
        access_token = create_access_token(user.id, user.login)
        new_refresh = uuid.uuid4().hex + uuid.uuid4().hex
        await self._repo.save_refresh_token(
            user_id=user.id,
            token=new_refresh,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        return RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ========================================================================
    # Me
    # ========================================================================

    async def get_me(self, user_id: UUID) -> MeResponse:
        # DEV bypass: return hardcoded admin profile when DEBUG=True
        if settings.DEBUG:
            dev_user = UserResponse(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                login="admin",
                full_name="Admin",
                email=None,
                employee_id=None,
                is_active=True,
                role_id=UUID("00000000-0000-0000-0000-000000000002"),
                last_login=None,
                created_at=datetime.now(timezone.utc),
            )
            dev_role = RoleResponse(
                id=UUID("00000000-0000-0000-0000-000000000002"),
                code="ADMIN",
                name="\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440",
                description="Development administrator",
                permissions=[],
            )
            return MeResponse(
                user=dev_user,
                role=dev_role,
                permissions=["SECURITY_MANAGE", "SETTINGS_EDIT", "PAYROLL_CALCULATE",
                            "PAYROLL_APPROVE", "PAYMENT_CREATE", "PAYMENT_POST"],
            )

        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundException("Пользователь не найден")
        role = user.role
        perms = [p.code for p in (role.permissions if role else [])]
        return MeResponse(
            user=UserResponse.model_validate(user),
            role=RoleResponse.model_validate(role) if role else None,
            permissions=perms,
        )

    # ========================================================================
    # Users
    # ========================================================================

    async def create_user(self, payload: UserCreate) -> UserResponse:
        existing = await self._repo.get_user_by_login(payload.login)
        if existing is not None:
            raise ConflictException(f"Пользователь '{payload.login}' уже существует")
        user = await self._repo.create_user(
            login=payload.login,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            email=payload.email,
            employee_id=payload.employee_id,
            role_id=payload.role_id,
        )
        return UserResponse.model_validate(user)

    async def get_users(self, *, page: int = 1, size: int = 100) -> list[UserResponse]:
        items, _ = await self._repo.get_all_users(
            offset=(page - 1) * size, limit=size
        )
        return [UserResponse.model_validate(u) for u in items]

    async def update_user(self, user_id: UUID, payload: UserUpdate) -> UserResponse:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundException(f"Пользователь с id={user_id} не найден")
        updated = await self._repo.update_user(
            user, **payload.model_dump(exclude_none=True)
        )
        return UserResponse.model_validate(updated)

    # ========================================================================
    # Roles
    # ========================================================================

    async def create_role(self, payload: RoleCreate) -> RoleResponse:
        existing = await self._repo.get_role_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Роль '{payload.code}' уже существует")
        role = await self._repo.create_role(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            permission_ids=payload.permission_ids,
        )
        return RoleResponse.model_validate(role)

    async def get_roles(self) -> list[RoleResponse]:
        items = await self._repo.get_all_roles()
        return [RoleResponse.model_validate(r) for r in items]

    async def seed_default_roles(self) -> list[RoleResponse]:
        defaults = [
            {"code": "ADMIN", "name": "Администратор"},
            {"code": "HR", "name": "Отдел кадров"},
            {"code": "ACCOUNTANT", "name": "Бухгалтер"},
            {"code": "MANAGER", "name": "Руководитель"},
            {"code": "EMPLOYEE", "name": "Сотрудник"},
        ]
        created: list[RoleResponse] = []
        for d in defaults:
            existing = await self._repo.get_role_by_code(d["code"])
            if existing is None:
                role = await self._repo.create_role(**d, permission_ids=[])
                created.append(RoleResponse(id=role.id, code=role.code, name=role.name, description=role.description, permissions=[]))
        return created

    # ========================================================================
    # Permissions
    # ========================================================================

    async def create_permission(self, payload: PermissionCreate) -> PermissionResponse:
        existing = await self._repo.get_permission_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Право '{payload.code}' уже существует")
        perm = await self._repo.create_permission(**payload.model_dump())
        return PermissionResponse.model_validate(perm)

    async def get_permissions(self) -> list[PermissionResponse]:
        items = await self._repo.get_all_permissions()
        return [PermissionResponse.model_validate(p) for p in items]

    async def seed_default_permissions(self) -> list[PermissionResponse]:
        defaults = [
            {"code": "EMPLOYEES_VIEW", "name": "Просмотр сотрудников", "module": "employees", "action": "view"},
            {"code": "EMPLOYEES_EDIT", "name": "Редактирование сотрудников", "module": "employees", "action": "edit"},
            {"code": "TIMESHEET_VIEW", "name": "Просмотр табеля", "module": "timesheets", "action": "view"},
            {"code": "TIMESHEET_EDIT", "name": "Редактирование табеля", "module": "timesheets", "action": "edit"},
            {"code": "TIMESHEET_APPROVE", "name": "Утверждение табеля", "module": "timesheets", "action": "approve"},
            {"code": "PAYROLL_CALCULATE", "name": "Расчёт зарплаты", "module": "payroll", "action": "calculate"},
            {"code": "PAYROLL_APPROVE", "name": "Утверждение расчёта", "module": "payroll", "action": "approve"},
            {"code": "PAYMENT_CREATE", "name": "Создание выплат", "module": "payments", "action": "create"},
            {"code": "PAYMENT_POST", "name": "Проведение выплат", "module": "payments", "action": "post"},
            {"code": "SETTINGS_EDIT", "name": "Изменение настроек", "module": "settings", "action": "edit"},
            {"code": "SECURITY_MANAGE", "name": "Управление доступом", "module": "security", "action": "manage"},
            {"code": "AUDIT_VIEW", "name": "Просмотр аудита", "module": "audit", "action": "view"},
        ]
        created: list[PermissionResponse] = []
        for d in defaults:
            existing = await self._repo.get_permission_by_code(d["code"])
            if existing is None:
                perm = await self._repo.create_permission(**d)
                created.append(PermissionResponse.model_validate(perm))
        return created
