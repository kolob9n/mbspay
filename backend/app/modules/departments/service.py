"""Department service — business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.departments.repository import DepartmentRepository
from app.modules.departments.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.shared.exceptions import ConflictException, NotFoundException


class DepartmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = DepartmentRepository(session)

    async def create(self, payload: DepartmentCreate) -> DepartmentResponse:
        existing = await self._repo.get_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Подразделение с кодом '{payload.code}' уже существует.")
        dept = await self._repo.create(name=payload.name, code=payload.code)
        return DepartmentResponse.model_validate(dept)

    async def get_by_id(self, dept_id: UUID) -> DepartmentResponse:
        dept = await self._repo.get_by_id(dept_id)
        if dept is None:
            raise NotFoundException(f"Подразделение с id={dept_id} не найдено.")
        return DepartmentResponse.model_validate(dept)

    async def get_all(self, *, page: int = 1, size: int = 100) -> list[DepartmentResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(offset=offset, limit=size)
        return [DepartmentResponse.model_validate(d) for d in items]

    async def update(self, dept_id: UUID, payload: DepartmentUpdate) -> DepartmentResponse:
        dept = await self._repo.get_by_id(dept_id)
        if dept is None:
            raise NotFoundException(f"Подразделение с id={dept_id} не найдено.")

        if payload.code is not None:
            dup = await self._repo.get_by_code(payload.code)
            if dup is not None and dup.id != dept_id:
                raise ConflictException(f"Код '{payload.code}' уже занят.")

        updated = await self._repo.update(
            dept,
            name=payload.name,
            code=payload.code,
            is_active=payload.is_active,
        )
        return DepartmentResponse.model_validate(updated)
