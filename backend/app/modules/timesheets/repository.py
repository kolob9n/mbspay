"""Timesheet repository — database access layer."""

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.timesheets.models import (
    Timesheet,
    TimesheetEntry,
    TimesheetStatus,
)


class TimesheetRepository:
    """All database queries for Timesheet and TimesheetEntry."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ========================================================================
    # Timesheet CRUD
    # ========================================================================

    async def create(
        self,
        *,
        payroll_period_id: UUID,
        department_id: UUID,
        created_by: UUID | None = None,
    ) -> Timesheet:
        ts = Timesheet(
            payroll_period_id=payroll_period_id,
            department_id=department_id,
            status=TimesheetStatus.DRAFT,
            created_by=created_by,
        )
        self._session.add(ts)
        await self._session.flush()
        return ts

    async def get_by_id(
        self, ts_id: UUID, *, with_entries: bool = False
    ) -> Timesheet | None:
        stmt = select(Timesheet).where(Timesheet.id == ts_id)
        if with_entries:
            stmt = stmt.options(
                joinedload(Timesheet.entries)
                .joinedload(TimesheetEntry.employee),
                joinedload(Timesheet.entries)
                .joinedload(TimesheetEntry.attendance_type),
            )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_all(
        self,
        *,
        department_id: UUID | None = None,
        status: TimesheetStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Timesheet], int]:
        base = select(Timesheet)
        if department_id is not None:
            base = base.where(Timesheet.department_id == department_id)
        if status is not None:
            base = base.where(Timesheet.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        items_stmt = (
            base.order_by(Timesheet.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(items_stmt)
        return list(result.scalars().all()), total

    async def check_exists(
        self, payroll_period_id: UUID, department_id: UUID
    ) -> bool:
        stmt = select(func.count(Timesheet.id)).where(
            Timesheet.payroll_period_id == payroll_period_id,
            Timesheet.department_id == department_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    # ========================================================================
    # TimesheetEntry — bulk generation
    # ========================================================================

    async def create_entries_bulk(
        self, entries: list[dict]
    ) -> list[TimesheetEntry]:
        """Bulk-insert timesheet entries. Each dict must have all required fields."""
        orm_entries = [TimesheetEntry(**e) for e in entries]
        self._session.add_all(orm_entries)
        await self._session.flush()
        return orm_entries

    # ========================================================================
    # TimesheetEntry — read
    # ========================================================================

    async def get_entry(self, entry_id: UUID) -> TimesheetEntry | None:
        stmt = (
            select(TimesheetEntry)
            .options(
                joinedload(TimesheetEntry.employee),
                joinedload(TimesheetEntry.attendance_type),
            )
            .where(TimesheetEntry.id == entry_id)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_entries_by_timesheet(
        self, timesheet_id: UUID
    ) -> list[TimesheetEntry]:
        stmt = (
            select(TimesheetEntry)
            .options(
                joinedload(TimesheetEntry.employee),
                joinedload(TimesheetEntry.attendance_type),
            )
            .where(TimesheetEntry.timesheet_id == timesheet_id)
            .order_by(TimesheetEntry.employee_id, TimesheetEntry.date)
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    # ========================================================================
    # TimesheetEntry — update
    # ========================================================================

    async def update_entry(
        self, entry: TimesheetEntry, **values
    ) -> TimesheetEntry:
        for key, val in values.items():
            if val is not None:
                setattr(entry, key, val)
        await self._session.flush()
        return entry

    # ========================================================================
    # Timesheet — workflow
    # ========================================================================

    async def submit(self, ts: Timesheet) -> Timesheet:
        ts.status = TimesheetStatus.SUBMITTED
        await self._session.flush()
        return ts

    async def approve(self, ts: Timesheet, approved_by: UUID) -> Timesheet:
        ts.status = TimesheetStatus.APPROVED
        ts.approved_by = approved_by
        ts.approved_at = datetime.now(timezone.utc)
        await self._session.flush()
        return ts

    async def return_to_revision(self, ts: Timesheet) -> Timesheet:
        ts.status = TimesheetStatus.RETURNED
        await self._session.flush()
        return ts

    async def close(self, ts: Timesheet) -> Timesheet:
        ts.status = TimesheetStatus.CLOSED
        await self._session.flush()
        return ts

    # ========================================================================
    # Summary calculation
    # ========================================================================

    async def calculate_summary(
        self, timesheet_id: UUID
    ) -> dict[str, int]:
        """Returns aggregated counts by attendance type code."""
        from app.modules.attendance_types.models import AttendanceType

        stmt = (
            select(
                AttendanceType.code,
                func.count(TimesheetEntry.id).label("cnt"),
                func.coalesce(func.sum(TimesheetEntry.hours), 0).label("hrs"),
            )
            .join(
                TimesheetEntry,
                TimesheetEntry.attendance_type_id == AttendanceType.id,
            )
            .where(TimesheetEntry.timesheet_id == timesheet_id)
            .group_by(AttendanceType.code)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        summary: dict[str, int] = {
            "worked_days": 0,
            "worked_hours": 0,
            "vacation_days": 0,
            "sick_days": 0,
            "overtime_hours": 0,
            "absence_days": 0,
            "business_trip_days": 0,
        }

        for code, cnt, hrs in rows:
            if code == "WORK":
                summary["worked_days"] = cnt
                summary["worked_hours"] = hrs
            elif code == "VACATION":
                summary["vacation_days"] = cnt
            elif code == "SICK":
                summary["sick_days"] = cnt
            elif code == "OVERTIME":
                summary["overtime_hours"] = hrs
            elif code == "ABSENCE":
                summary["absence_days"] = cnt
            elif code == "BUSINESS_TRIP":
                summary["business_trip_days"] = cnt

        return summary

    async def calculate_summary_for_employee(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> dict[str, int]:
        """Aggregate timesheet data for one employee in a period."""
        from app.modules.attendance_types.models import AttendanceType

        stmt = (
            select(
                func.count(TimesheetEntry.id).label("cnt"),
                func.coalesce(func.sum(TimesheetEntry.hours), 0).label("hrs"),
            )
            .join(
                AttendanceType,
                TimesheetEntry.attendance_type_id == AttendanceType.id,
            )
            .where(
                TimesheetEntry.employee_id == employee_id,
                AttendanceType.code == "WORK",
            )
        )
        # Get the timesheet for this employee in this period
        sub = (
            select(TimesheetEntry)
            .join(Timesheet, TimesheetEntry.timesheet_id == Timesheet.id)
            .where(
                TimesheetEntry.employee_id == employee_id,
                Timesheet.payroll_period_id == payroll_period_id,
            )
            .subquery()
        )

        stmt2 = (
            select(
                func.count(sub.c.id),
                func.coalesce(func.sum(sub.c.hours), 0),
            )
            .select_from(sub)
            .join(
                AttendanceType,
                sub.c.attendance_type_id == AttendanceType.id,
            )
            .where(AttendanceType.code == "WORK")
        )
        result = await self._session.execute(stmt2)
        row = result.one()
        return {"worked_days": int(row[0]), "worked_hours": int(row[1])}
