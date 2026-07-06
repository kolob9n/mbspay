"""AttendanceType repository — database access layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance_types.models import AttendanceType


class AttendanceTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **values) -> AttendanceType:
        at = AttendanceType(**values)
        self._session.add(at)
        await self._session.flush()
        return at

    async def get_by_id(self, at_id: UUID) -> AttendanceType | None:
        stmt = select(AttendanceType).where(AttendanceType.id == at_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> AttendanceType | None:
        stmt = select(AttendanceType).where(AttendanceType.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[AttendanceType]:
        stmt = (
            select(AttendanceType)
            .where(AttendanceType.is_active == True)  # noqa: E712
            .order_by(AttendanceType.code)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self) -> list[AttendanceType]:
        stmt = select(AttendanceType).order_by(AttendanceType.code)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, at: AttendanceType, **values) -> AttendanceType:
        for key, val in values.items():
            if val is not None:
                setattr(at, key, val)
        await self._session.flush()
        return at
