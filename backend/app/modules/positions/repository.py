"""Position repository — database access layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.positions.models import Position


class PositionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, name: str, code: str) -> Position:
        pos = Position(name=name, code=code)
        self._session.add(pos)
        await self._session.flush()
        return pos

    async def get_by_id(self, pos_id: UUID) -> Position | None:
        stmt = select(Position).where(Position.id == pos_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Position | None:
        stmt = select(Position).where(Position.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[Position], int]:
        base = select(Position)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(Position.name).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update(self, position: Position, **values) -> Position:
        for key, val in values.items():
            if val is not None:
                setattr(position, key, val)
        await self._session.flush()
        return position
