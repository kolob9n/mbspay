"""Workflow Engine — universal state machine for all document types.

Model-driven: states and transitions are stored in DB, not hardcoded.
Supports: Timesheet, Payment, PayrollRun, Calendar, and any future document.

Usage::

    engine = WorkflowEngine(session)
    can_transition = await engine.can_transition("timesheet", "DRAFT", "SUBMITTED")
    await engine.transition(timesheet_doc, "SUBMITTED")
"""

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class WorkflowEngine:
    """Universal workflow engine.

    Checks and executes state transitions for any document type.
    Supports permission-based transition guards.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        from app.shared.workflow.repository import WorkflowRepository
        self._repo = WorkflowRepository(session)

    async def can_transition(
        self,
        document_type: str,
        from_state: str,
        to_state: str,
    ) -> bool:
        """Check if a transition is allowed."""
        return await self._repo.transition_exists(
            document_type, from_state, to_state
        )

    async def transition(
        self,
        document: Any,
        to_state: str,
        *,
        user_id: Optional[str] = None,
    ) -> Any:
        """Execute a state transition on a document.

        Args:
            document: ORM object with ``status`` attribute (Enum or str).
            to_state: Target state code.
            user_id: Optional user performing the transition (for audit).

        Returns:
            The updated document.

        Raises:
            BusinessRuleException: If transition is not allowed.
        """
        from_state = document.status.value if hasattr(document.status, 'value') else str(document.status)

        allowed = await self.can_transition(
            document.__class__.__name__.lower(), from_state, to_state
        )

        if not allowed:
            from app.shared.exceptions import BusinessRuleException
            raise BusinessRuleException(
                f"Переход из '{from_state}' в '{to_state}' не разрешён."
            )

        # Update status
        if hasattr(document.status, 'value'):
            # Enum — need to set to the enum value
            enum_cls = type(document.status)
            try:
                document.status = enum_cls(to_state)
            except ValueError:
                document.status = to_state
        else:
            document.status = to_state

        await self._session.flush()

        # Audit log
        from app.shared.audit.audit_logger import audit_logger
        await audit_logger.log(
            action="TRANSITION",
            entity=document.__class__.__name__,
            entity_id=str(document.id),
            user_id=user_id,
            changes={"from_state": from_state, "to_state": to_state},
        )

        return document

    async def get_available_transitions(
        self, document_type: str, current_state: str
    ) -> list[str]:
        """Get list of allowed next states."""
        return await self._repo.get_next_states(document_type, current_state)

    async def seed_defaults(self) -> None:
        """Create default workflow definitions for all document types."""
        defaults = {
            "timesheet": [
                ("DRAFT", "SUBMITTED", "TIMESHEET_EDIT"),
                ("SUBMITTED", "APPROVED", "TIMESHEET_APPROVE"),
                ("SUBMITTED", "RETURNED", "TIMESHEET_EDIT"),
                ("RETURNED", "SUBMITTED", "TIMESHEET_EDIT"),
                ("APPROVED", "CLOSED", "TIMESHEET_APPROVE"),
                ("DRAFT", "CLOSED", "TIMESHEET_EDIT"),
            ],
            "payment": [
                ("DRAFT", "POSTED", "PAYMENT_POST"),
                ("POSTED", "CANCELLED", "PAYMENT_POST"),
            ],
            "payrollrun": [
                ("DRAFT", "CALCULATED", "PAYROLL_CALCULATE"),
                ("CALCULATED", "APPROVED", "PAYROLL_APPROVE"),
                ("CALCULATED", "DRAFT", "PAYROLL_CALCULATE"),
                ("APPROVED", "CLOSED", "PAYROLL_APPROVE"),
                ("DRAFT", "CANCELLED", "PAYROLL_CALCULATE"),
                ("CALCULATED", "CANCELLED", "PAYROLL_APPROVE"),
            ],
            "calendaryear": [
                ("DRAFT", "APPROVED", "SETTINGS_EDIT"),
            ],
        }

        for doc_type, transitions in defaults.items():
            for from_s, to_s, perm in transitions:
                exists = await self._repo.transition_exists(doc_type, from_s, to_s)
                if not exists:
                    await self._repo.create_transition(
                        document_type=doc_type,
                        from_state=from_s,
                        to_state=to_s,
                        permission=perm,
                    )
