"""Audit API — HTTP layer (read-only)."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.audit.repository import AuditRepository
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/")
async def list_audit(
    db: Annotated[AsyncSession, Depends(get_db)],
    entity: Annotated[Optional[str], Query()] = None,
    entity_id: Annotated[Optional[str], Query()] = None,
    operation: Annotated[Optional[str], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 100,
):
    repo = AuditRepository(db)
    offset = (page - 1) * size
    items, total = await repo.get_all(
        entity=entity, entity_id=entity_id, operation=operation,
        offset=offset, limit=size,
    )
    return ApiResponse.ok({
        "items": [
            {
                "id": str(e.id),
                "user_id": str(e.user_id) if e.user_id else None,
                "entity": e.entity,
                "entity_id": e.entity_id,
                "operation": e.operation,
                "old_value": e.old_value,
                "new_value": e.new_value,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in items
        ],
        "total": total,
    })
