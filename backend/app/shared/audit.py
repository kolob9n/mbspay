"""Audit trail — placeholder for future implementation.

Will track:
- Who performed an action
- What action was performed
- On which entity
- Old / new values (diff)
- Timestamp
"""


class AuditLogger:
    """Stub — will be implemented in a future iteration."""

    @staticmethod
    async def log(
        *,
        action: str,
        entity: str,
        entity_id: str,
        user_id: str | None = None,
        changes: dict | None = None,
    ) -> None:
        """Placeholder for audit logging."""
        pass


audit_logger = AuditLogger()
