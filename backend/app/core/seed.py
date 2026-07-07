"""Auto-seed system data on startup - idempotent, safe for dev and CI.

Called from main.py lifespan startup. Every seed check is idempotent
(existing records are skipped).

Seed order matters:
  1. Settings       - system constants (BASE_PERCENT, KPI_PERCENT, ...)
  2. AttendanceTypes - WORK, WEEKEND, HOLIDAY, etc.
  3. Permissions    - CRUD rights per module
  4. Roles          - ADMIN, HR, ACCOUNTANT, MANAGER, EMPLOYEE
  5. Workflow       - allowed state transitions for all document types
  6. Admin user     - dev login admin/admin (ATTENTION: change in production!)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


async def seed_all(session: AsyncSession) -> dict[str, int]:
    """Run all seeds. Returns dict of {module: count_created}."""
    results: dict[str, int] = {}

    # 1. Settings
    from app.modules.settings.service import SettingsService
    svc = SettingsService(session)
    created = await svc.seed_defaults()
    results["settings"] = len(created)

    # 2. Attendance types
    from app.modules.attendance_types.service import AttendanceTypeService
    at_svc = AttendanceTypeService(session)
    created = await at_svc.seed_defaults()
    results["attendance_types"] = len(created)

    # 3. Permissions
    from app.modules.security.service import SecurityService
    sec_svc = SecurityService(session)
    created = await sec_svc.seed_default_permissions()
    results["permissions"] = len(created)

    # 4. Roles
    created = await sec_svc.seed_default_roles()
    results["roles"] = len(created)

    # 5. Workflow transitions
    from app.shared.workflow.engine import WorkflowEngine
    wf = WorkflowEngine(session)
    await wf.seed_defaults()
    results["workflow"] = 1  # qualitative

    # 6. Dev admin user (login: admin, password: admin) - only in DEBUG mode
    if settings.DEBUG:
        from app.modules.security.repository import SecurityRepository
        sec_repo = SecurityRepository(session)
        from app.core.security import hash_password

        existing_admin = await sec_repo.get_user_by_login("admin")
        if existing_admin is None:
            admin_role = await sec_repo.get_role_by_code("ADMIN")
            if admin_role is not None:
                all_perms = await sec_repo.get_all_permissions()
                admin_role.permissions = all_perms
                await sec_repo.create_user(
                    login="admin",
                    password_hash=hash_password("admin"),
                    full_name="Admin",
                    role_id=admin_role.id,
                )
                results["admin_user"] = 1
            else:
                results["admin_user"] = 0
        else:
            results["admin_user"] = 0
    else:
        results["admin_user"] = 0

    await session.commit()
    return results
