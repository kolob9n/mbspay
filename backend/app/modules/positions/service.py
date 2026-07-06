"""Position service — business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.positions.repository import PositionRepository
from app.modules.positions.schemas import (
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)
from app.shared.exceptions import ConflictException, NotFoundException


class PositionService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = PositionRepository(session)

    async def create(self, payload: PositionCreate) -> PositionResponse:
        existing = await self._repo.get_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Должность с кодом '{payload.code}' уже существует.")
        pos = await self._repo.create(name=payload.name, code=payload.code)
        return PositionResponse.model_validate(pos)

    async def get_by_id(self, pos_id: UUID) -> PositionResponse:
        pos = await self._repo.get_by_id(pos_id)
        if pos is None:
            raise NotFoundException(f"Должность с id={pos_id} не найдена.")
        return PositionResponse.model_validate(pos)

    async def get_all(self, *, page: int = 1, size: int = 100) -> list[PositionResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(offset=offset, limit=size)
        return [PositionResponse.model_validate(p) for p in items]

    async def update(self, pos_id: UUID, payload: PositionUpdate) -> PositionResponse:
        pos = await self._repo.get_by_id(pos_id)
        if pos is None:
            raise NotFoundException(f"Должность с id={pos_id} не найдена.")

        if payload.code is not None:
            dup = await self._repo.get_by_code(payload.code)
            if dup is not None and dup.id != pos_id:
                raise ConflictException(f"Код '{payload.code}' уже занят.")

        updated = await self._repo.update(
            pos,
            name=payload.name,
            code=payload.code,
            is_active=payload.is_active,
        )
        return PositionResponse.model_validate(updated)
