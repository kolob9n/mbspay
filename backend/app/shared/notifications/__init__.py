"""Notifications service — stub."""

from typing import Any


class NotificationService:
    """Placeholder notification service."""

    async def send(self, *, user_id: str, title: str, body: str) -> None:
        pass

    async def notify_user(self, user_id: str, message: str) -> None:
        pass

    async def notify_role(self, role_code: str, message: str) -> None:
        pass
