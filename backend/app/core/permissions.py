"""Permission system — placeholder for future RBAC implementation."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> str:
    """Stub — will decode JWT and return user_id in the future."""
    # Placeholder: return a dummy user
    return "system"


# ---- Permission stubs ---------------------------------------------------
class Requires:
    """Fluent permission DSL (stub)."""

    @staticmethod
    def any(*perms: str):
        """Placeholder — require any of the listed permissions."""
        return Depends(get_current_user)

    @staticmethod
    def all(*perms: str):
        """Placeholder — require all of the listed permissions."""
        return Depends(get_current_user)
