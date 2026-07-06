"""Background Tasks — stub."""

from typing import Any


class TaskManager:
    """Placeholder background task manager."""

    async def enqueue(self, task_name: str, payload: dict[str, Any]) -> str:
        return "task-id-placeholder"

    async def run(self, task_id: str) -> None:
        pass

    async def cancel(self, task_id: str) -> None:
        pass

    async def status(self, task_id: str) -> str:
        return "pending"
