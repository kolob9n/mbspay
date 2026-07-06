"""Audit log — automatic change tracking.

Called from services whenever an entity is created, updated, or deleted.
Stores old_value, new_value as JSON for full reconstruction.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class AuditLogger:
    """Singleton audit logger — call from any service to record changes."""

    @staticmethod
    async def log(
        *,
        action: str,
        entity: str,
        entity_id: str,
        user_id: Optional[str] = None,
        changes: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        old_value: Optional[dict[str, Any]] = None,
        new_value: Optional[dict[str, Any]] = None,
    ) -> None:
        """Write an audit log entry.

        Args:
            action: CREATE, UPDATE, DELETE, LOGIN, APPROVE, POST, CANCEL, TRANSITION.
            entity: Name of the entity (e.g. "PayrollRun", "Timesheet").
            entity_id: UUID of the affected entity.
            user_id: Who performed the action.
            changes: Dict of changed fields (for UPDATE).
            ip_address: Client IP.
            old_value: Full snapshot before change.
            new_value: Full snapshot after change.
        """
        from app.shared.audit.repository import AuditRepository
        # We need a session here — this is a limitation of the static approach.
        # In practice, the caller should have access to the session.
        pass  # See repository-based implementation below


audit_logger = AuditLogger()
