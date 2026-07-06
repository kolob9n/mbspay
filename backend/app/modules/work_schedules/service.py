"""WorkSchedule service — business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.work_schedules.repository import WorkScheduleRepository
from app.modules.work_schedules.schemas import (
    WorkScheduleCreate,
    WorkScheduleResponse,
    WorkScheduleUpdate,
)
from app.shared.exceptions import NotFoundException


class WorkScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = WorkScheduleRepository(session)

    async def create(self, payload: WorkScheduleCreate) -> WorkScheduleResponse:
        ws = await self._repo.create(
            name=payload.name,
            working_days=payload.working_days,
            working_hours=payload.working_hours,
        )
        return WorkScheduleResponse.model_validate(ws)

    async def get_by_id(self, ws_id: UUID) -> WorkScheduleResponse:
        ws = await self._repo.get_by_id(ws_id)
        if ws is None:
            raise NotFoundException(f"График с id={ws_id} не найден.")
        return WorkScheduleResponse.model_validate(ws)

    async def get_all(
        self, *, page: int = 1, size: int = 100
    ) -> list[WorkScheduleResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(offset=offset, limit=size)
        return [WorkScheduleResponse.model_validate(w) for w in items]

    async def update(
        self, ws_id: UUID, payload: WorkScheduleUpdate
    ) -> WorkScheduleResponse:
        ws = await self._repo.get_by_id(ws_id)
        if ws is None:
            raise NotFoundException(f"График с id={ws_id} не найден.")
        updated = await self._repo.update(
            ws,
            name=payload.name,
            working_days=payload.working_days,
            working_hours=payload.working_hours,
            is_active=payload.is_active,
        )
        return WorkScheduleResponse.model_validate(updated)
