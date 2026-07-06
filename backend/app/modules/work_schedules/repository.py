"""WorkSchedule repository — database access layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.work_schedules.models import WorkSchedule


class WorkScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, name: str, working_days: int, working_hours: int) -> WorkSchedule:
        ws = WorkSchedule(name=name, working_days=working_days, working_hours=working_hours)
        self._session.add(ws)
        await self._session.flush()
        return ws

    async def get_by_id(self, ws_id: UUID) -> WorkSchedule | None:
        stmt = select(WorkSchedule).where(WorkSchedule.id == ws_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[WorkSchedule], int]:
        base = select(WorkSchedule)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(WorkSchedule.name).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update(self, work_schedule: WorkSchedule, **values) -> WorkSchedule:
        for key, val in values.items():
            if val is not None:
                setattr(work_schedule, key, val)
        await self._session.flush()
        return work_schedule
