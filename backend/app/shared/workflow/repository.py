"""Workflow repository — database access layer for state machine definitions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.workflow.models import WorkflowTransition


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_transition(
        self,
        *,
        document_type: str,
        from_state: str,
        to_state: str,
        permission: str | None = None,
    ) -> WorkflowTransition:
        wt = WorkflowTransition(
            document_type=document_type,
            from_state=from_state,
            to_state=to_state,
            permission=permission,
        )
        self._session.add(wt)
        await self._session.flush()
        return wt

    async def transition_exists(
        self, document_type: str, from_state: str, to_state: str
    ) -> bool:
        stmt = select(WorkflowTransition).where(
            WorkflowTransition.document_type == document_type,
            WorkflowTransition.from_state == from_state,
            WorkflowTransition.to_state == to_state,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_next_states(
        self, document_type: str, current_state: str
    ) -> list[str]:
        stmt = select(WorkflowTransition.to_state).where(
            WorkflowTransition.document_type == document_type,
            WorkflowTransition.from_state == current_state,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
