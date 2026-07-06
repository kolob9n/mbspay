"""Alembic environment configuration — async."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.shared.base import Base

# Standard library imports
import os
import tempfile
import uuid as _uuid

# Import all models so Base.metadata is populated
import app.modules.attendance_types.models  # noqa: F401
import app.modules.calendar.models  # noqa: F401
import app.modules.defects.models  # noqa: F401
import app.modules.departments.models  # noqa: F401
import app.modules.employees.models  # noqa: F401
import app.modules.formula_engine.models  # noqa: F401
import app.modules.kpi.models  # noqa: F401
import app.modules.payments.models  # noqa: F401
import app.modules.payroll.models  # noqa: F401
import app.modules.payroll_ledger.models  # noqa: F401
import app.modules.payroll_periods.models  # noqa: F401
import app.modules.payslips.models  # noqa: F401
import app.modules.positions.models  # noqa: F401
import app.modules.timesheets.models  # noqa: F401
import app.modules.work_schedules.models  # noqa: F401

# Replace UUID function for mocks
_uuid4 = _uuid.uuid4

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
