"""Settings service — centralized configuration for all system modules."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.repository import SettingsRepository
from app.modules.settings.schemas import (
    SettingCreate,
    SettingResponse,
    SettingUpdate,
)
from app.shared.exceptions import ConflictException, NotFoundException

DEFAULT_SETTINGS: list[dict] = [
    {"key": "BASE_PERCENT", "value": "55", "value_type": "int", "description": "Базовая часть зарплаты (%)"},
    {"key": "KPI_PERCENT", "value": "45", "value_type": "int", "description": "Премиальная часть зарплаты (%)"},
    {"key": "DEFAULT_WORKDAY_HOURS", "value": "8", "value_type": "int", "description": "Часов в рабочем дне"},
    {"key": "ROUND_PRECISION", "value": "2", "value_type": "int", "description": "Точность округления"},
    {"key": "DEFAULT_CURRENCY", "value": "RUB", "value_type": "string", "description": "Валюта по умолчанию"},
    {"key": "ALLOW_RECALCULATION", "value": "true", "value_type": "bool", "description": "Разрешить пересчёт зарплаты"},
]


class SettingsService:
    """Centralized key-value configuration service.

    All services should read settings through this, not from hardcoded values.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SettingsRepository(session)

    async def seed_defaults(self) -> list[SettingResponse]:
        created: list[SettingResponse] = []
        for d in DEFAULT_SETTINGS:
            existing = await self._repo.get_by_key(d["key"])
            if existing is None:
                s = await self._repo.create(**d)
                created.append(SettingResponse.model_validate(s))
        return created

    async def get_all(self) -> list[SettingResponse]:
        items = await self._repo.get_all()
        return [SettingResponse.model_validate(i) for i in items]

    async def create(self, payload: SettingCreate) -> SettingResponse:
        existing = await self._repo.get_by_key(payload.key)
        if existing is not None:
            raise ConflictException(f"Настройка '{payload.key}' уже существует")
        s = await self._repo.create(**payload.model_dump())
        return SettingResponse.model_validate(s)

    async def update(self, key: str, payload: SettingUpdate) -> SettingResponse:
        s = await self._repo.get_by_key(key)
        if s is None:
            raise NotFoundException(f"Настройка '{key}' не найдена")
        updated = await self._repo.update(s, **payload.model_dump(exclude_none=True))
        return SettingResponse.model_validate(updated)

    # ---- Convenience methods ------------------------------------------------

    async def get_value(self, key: str, default: str = "") -> str:
        return await self._repo.get_value(key, default)

    async def get_int(self, key: str, default: int = 0) -> int:
        return await self._repo.get_int(key, default)

    async def get_bool(self, key: str, default: bool = False) -> bool:
        return await self._repo.get_bool(key, default)

    async def get_float(self, key: str, default: float = 0.0) -> float:
        return await self._repo.get_float(key, default)
