"""Audit repository — database access layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.audit.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID | None = None,
        entity: str,
        entity_id: str,
        operation: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            entity=entity,
            entity_id=entity_id,
            operation=operation,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_all(
        self,
        *,
        entity: str | None = None,
        entity_id: str | None = None,
        operation: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[AuditLog], int]:
        base = select(AuditLog)
        if entity:
            base = base.where(AuditLog.entity == entity)
        if entity_id:
            base = base.where(AuditLog.entity_id == entity_id)
        if operation:
            base = base.where(AuditLog.operation == operation)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        items_stmt = (
            base.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total
