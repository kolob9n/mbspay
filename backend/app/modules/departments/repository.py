"""Department repository — database access layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.departments.models import Department


class DepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, name: str, code: str) -> Department:
        dept = Department(name=name, code=code)
        self._session.add(dept)
        await self._session.flush()
        return dept

    async def get_by_id(self, dept_id: UUID) -> Department | None:
        stmt = select(Department).where(Department.id == dept_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Department | None:
        stmt = select(Department).where(Department.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[Department], int]:
        base = select(Department)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(Department.name).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update(self, department: Department, **values) -> Department:
        for key, val in values.items():
            if val is not None:
                setattr(department, key, val)
        await self._session.flush()
        return department
