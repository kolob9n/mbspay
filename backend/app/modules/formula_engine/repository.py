"""Formula repository — database access layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.formula_engine.models import Formula


class FormulaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **values) -> Formula:
        f = Formula(**values)
        self._session.add(f)
        await self._session.flush()
        return f

    async def get_by_id(self, formula_id: UUID) -> Formula | None:
        stmt = select(Formula).where(Formula.id == formula_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Formula | None:
        stmt = select(Formula).where(Formula.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[Formula], int]:
        base = select(Formula)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(Formula.code).offset(offset).limit(limit)
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def update(self, formula: Formula, **values) -> Formula:
        for key, val in values.items():
            if val is not None:
                setattr(formula, key, val)
        await self._session.flush()
        return formula
