"""AttendanceType service — business logic + seed data."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance_types.repository import AttendanceTypeRepository
from app.modules.attendance_types.schemas import (
    AttendanceTypeCreate,
    AttendanceTypeResponse,
    AttendanceTypeUpdate,
)
from app.shared.exceptions import ConflictException, NotFoundException

# ---- Default attendance types ----------------------------------------------

DEFAULT_ATTENDANCE_TYPES: list[dict] = [
    {"code": "WORK", "name": "Явка", "is_working_day": True, "is_paid": True,
     "counts_for_experience": True, "default_hours": 8, "color": "#4CAF50"},
    {"code": "WEEKEND", "name": "Выходной", "is_working_day": False, "is_paid": False,
     "counts_for_experience": False, "default_hours": 0, "color": "#9E9E9E"},
    {"code": "HOLIDAY", "name": "Праздник", "is_working_day": False, "is_paid": False,
     "counts_for_experience": False, "default_hours": 0, "color": "#FF5722"},
    {"code": "VACATION", "name": "Отпуск", "is_working_day": False, "is_paid": True,
     "counts_for_experience": True, "default_hours": 8, "color": "#2196F3"},
    {"code": "SICK", "name": "Больничный", "is_working_day": False, "is_paid": True,
     "counts_for_experience": True, "default_hours": 8, "color": "#FF9800"},
    {"code": "ABSENCE", "name": "Прогул", "is_working_day": False, "is_paid": False,
     "counts_for_experience": False, "default_hours": 8, "color": "#F44336"},
    {"code": "BUSINESS_TRIP", "name": "Командировка", "is_working_day": True,
     "is_paid": True, "counts_for_experience": True, "default_hours": 8,
     "color": "#9C27B0"},
    {"code": "OVERTIME", "name": "Сверхурочная работа", "is_working_day": True,
     "is_paid": True, "counts_for_experience": True, "default_hours": 0,
     "color": "#FFC107"},
]


class AttendanceTypeService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AttendanceTypeRepository(session)

    # ---- Seed --------------------------------------------------------------

    async def seed_defaults(self) -> list[AttendanceTypeResponse]:
        """Create default attendance types if they don't exist."""
        created: list[AttendanceTypeResponse] = []
        for item in DEFAULT_ATTENDANCE_TYPES:
            existing = await self._repo.get_by_code(item["code"])
            if existing is None:
                at = await self._repo.create(**item)
                created.append(AttendanceTypeResponse.model_validate(at))
        return created

    # ---- CRUD --------------------------------------------------------------

    async def get_all(self) -> list[AttendanceTypeResponse]:
        items = await self._repo.get_all()
        return [AttendanceTypeResponse.model_validate(i) for i in items]

    async def get_active(self) -> list[AttendanceTypeResponse]:
        items = await self._repo.get_all_active()
        return [AttendanceTypeResponse.model_validate(i) for i in items]

    async def create(self, payload: AttendanceTypeCreate) -> AttendanceTypeResponse:
        existing = await self._repo.get_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Тип '{payload.code}' уже существует.")
        at = await self._repo.create(**payload.model_dump())
        return AttendanceTypeResponse.model_validate(at)

    async def update(
        self, at_id: UUID, payload: AttendanceTypeUpdate
    ) -> AttendanceTypeResponse:
        at = await self._repo.get_by_id(at_id)
        if at is None:
            raise NotFoundException(f"Тип явки с id={at_id} не найден.")
        updated = await self._repo.update(at, **payload.model_dump(exclude_none=True))
        return AttendanceTypeResponse.model_validate(updated)
