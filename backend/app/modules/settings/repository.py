"""Settings repository — database access layer."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.models import Setting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **values) -> Setting:
        s = Setting(**values)
        self._session.add(s)
        await self._session.flush()
        return s

    async def get_by_key(self, key: str) -> Setting | None:
        stmt = select(Setting).where(Setting.key == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Setting]:
        stmt = select(Setting).order_by(Setting.key)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, setting: Setting, **values) -> Setting:
        for k, v in values.items():
            if v is not None:
                setattr(setting, k, v)
        await self._session.flush()
        return setting

    async def get_value(self, key: str, default: str = "") -> str:
        s = await self.get_by_key(key)
        return s.value if s else default

    async def get_int(self, key: str, default: int = 0) -> int:
        val = await self.get_value(key, str(default))
        try:
            return int(val)
        except ValueError:
            return default

    async def get_bool(self, key: str, default: bool = False) -> bool:
        val = await self.get_value(key, str(default).lower())
        return val.lower() in ("true", "1", "yes")

    async def get_float(self, key: str, default: float = 0.0) -> float:
        val = await self.get_value(key, str(default))
        try:
            return float(val)
        except ValueError:
            return default
