"""Security repository — database access layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.security.models import (
    Permission,
    RefreshToken,
    Role,
    User,
)


class SecurityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # User
    # ========================================================================

    async def create_user(self, **values) -> User:
        u = User(**values)
        self._session.add(u)
        await self._session.flush()
        return u

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_login(self, login: str) -> User | None:
        stmt = select(User).where(User.login == login)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_users(
        self, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[User], int]:
        base = select(User)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(User.login).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update_user(self, user: User, **values) -> User:
        for key, val in values.items():
            if val is not None:
                setattr(user, key, val)
        await self._session.flush()
        return user

    # ========================================================================
    # RefreshToken
    # ========================================================================

    async def save_refresh_token(
        self, *, user_id: UUID, token: str, expires_at: datetime
    ) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
        self._session.add(rt)
        await self._session.flush()
        return rt

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================================================
    # Role
    # ========================================================================

    async def create_role(
        self, *, code: str, name: str, description: str | None = None,
        permission_ids: list[UUID] | None = None,
    ) -> Role:
        role = Role(code=code, name=name, description=description)
        if permission_ids:
            perms = await self._get_permissions_by_ids(permission_ids)
            role.permissions = perms
        self._session.add(role)
        await self._session.flush()
        return role

    async def get_role_by_code(self, code: str) -> Role | None:
        stmt = select(Role).where(Role.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_role_by_id(self, role_id: UUID) -> Role | None:
        stmt = select(Role).where(Role.id == role_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> list[Role]:
        stmt = select(Role).order_by(Role.code)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ========================================================================
    # Permission
    # ========================================================================

    async def create_permission(self, **values) -> Permission:
        p = Permission(**values)
        self._session.add(p)
        await self._session.flush()
        return p

    async def get_permission_by_code(self, code: str) -> Permission | None:
        stmt = select(Permission).where(Permission.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_permissions(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.module, Permission.code)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _get_permissions_by_ids(
        self, ids: list[UUID]
    ) -> list[Permission]:
        stmt = select(Permission).where(Permission.id.in_(ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
