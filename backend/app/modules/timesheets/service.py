"""Timesheet service — business logic for timesheet management."""

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance_types.repository import AttendanceTypeRepository
from app.modules.calendar.repository import CalendarRepository
from app.modules.departments.repository import DepartmentRepository
from app.modules.employees.repository import EmployeeRepository
from app.modules.payroll_periods.repository import PayrollPeriodRepository
from app.modules.timesheets.models import Timesheet, TimesheetStatus
from app.modules.timesheets.repository import TimesheetRepository
from app.modules.timesheets.schemas import (
    MatrixDayItem,
    MatrixEmployeeRow,
    TimesheetCreate,
    TimesheetDetailResponse,
    TimesheetEntryResponse,
    TimesheetEntryUpdate,
    TimesheetMatrixResponse,
    TimesheetResponse,
    TimesheetSummaryResponse,
)
from app.shared.exceptions import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
)


class TimesheetService:
    """Timesheet domain logic — auto-fill, workflow, matrix, summary.

    No SQLAlchemy here — only Repository calls and business rules.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TimesheetRepository(session)
        self._period_repo = PayrollPeriodRepository(session)
        self._dept_repo = DepartmentRepository(session)
        self._emp_repo = EmployeeRepository(session)
        self._cal_repo = CalendarRepository(session)
        self._at_repo = AttendanceTypeRepository(session)

    # ========================================================================
    # Create + auto-fill
    # ========================================================================

    async def create_timesheet(
        self, payload: TimesheetCreate, *, created_by: UUID | None = None
    ) -> TimesheetDetailResponse:
        """Create a new timesheet and auto-fill from calendar + employees."""

        # Validate period
        period = await self._period_repo.get_by_id(payload.payroll_period_id)
        if period is None:
            raise NotFoundException("Период не найден.")

        # Validate department
        dept = await self._dept_repo.get_by_id(payload.department_id)
        if dept is None:
            raise NotFoundException("Подразделение не найдено.")

        # Rule: only one timesheet per period+department
        exists = await self._repo.check_exists(
            payload.payroll_period_id, payload.department_id
        )
        if exists:
            raise ConflictException(
                f"Табель для подразделения '{dept.name}' "
                f"за период {period.period_label} уже существует."
            )

        # Create timesheet
        ts = await self._repo.create(
            payroll_period_id=payload.payroll_period_id,
            department_id=payload.department_id,
            created_by=created_by,
        )

        # Auto-generate entries
        await self._generate_entries(ts, period.year, period.month)

        return await self._get_detail(ts.id)

    async def _generate_entries(
        self, ts: Timesheet, year: int, month: int
    ) -> None:
        """Auto-fill: employees × calendar days = timesheet entries."""

        # 1. Get active employees in department
        employees, _ = await self._emp_repo.get_all(
            is_active=True, department_id=ts.department_id, limit=10_000
        )
        if not employees:
            return

        # 2. Get calendar data
        cal_year = await self._cal_repo.get_year_by_number(year)

        # 3. Get attendance types lookup
        at_work = await self._at_repo.get_by_code("WORK")
        at_weekend = await self._at_repo.get_by_code("WEEKEND")
        at_holiday = await self._at_repo.get_by_code("HOLIDAY")
        at_short_day = await self._at_repo.get_by_code("WORK")  # short day → WORK

        # 4. Calendar-day-type → attendance-type mapping
        from app.modules.calendar.models import DayType

        day_type_map = {
            DayType.WORKDAY: at_work,
            DayType.WEEKEND: at_weekend,
            DayType.HOLIDAY: at_holiday,
            DayType.SHORT_DAY: at_short_day,
            DayType.CUSTOM: at_work,
        }

        # 5. Build calendar lookups
        cal_by_date: dict[date, tuple[bool, int, UUID | None]] = {}
        if cal_year is not None:
            cal_days = await self._cal_repo.get_days_by_month(cal_year.id, month)
            for cd in cal_days:
                at_for_type = day_type_map.get(cd.day_type, at_work)
                cal_by_date[cd.date] = (
                    cd.is_working_day,
                    cd.working_hours,
                    at_for_type.id if at_for_type else None,
                )

        # 6. Generate entries
        import calendar as py_cal
        days_in_month = py_cal.monthrange(year, month)[1]

        entries: list[dict] = []
        for emp in employees:
            for day in range(1, days_in_month + 1):
                dt = date(year, month, day)

                if dt in cal_by_date:
                    is_working, hours, at_id = cal_by_date[dt]
                else:
                    # No calendar — fallback to weekday rule
                    weekday = dt.weekday()
                    is_working = weekday < 5
                    hours = 8 if is_working else 0
                    at_id = at_work.id if is_working else at_weekend.id if at_weekend else None

                if at_id is None:
                    at_id = at_work.id if at_work else None
                if at_id is None:
                    continue

                entries.append({
                    "timesheet_id": ts.id,
                    "employee_id": emp.id,
                    "date": dt,
                    "attendance_type_id": at_id,
                    "hours": hours,
                })

        if entries:
            await self._repo.create_entries_bulk(entries)

    # ========================================================================
    # Read
    # ========================================================================

    async def get_timesheet(self, ts_id: UUID) -> TimesheetDetailResponse:
        return await self._get_detail(ts_id)

    async def get_all(
        self,
        *,
        department_id: UUID | None = None,
        status: TimesheetStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[TimesheetResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(
            department_id=department_id, status=status,
            offset=offset, limit=size,
        )
        return [TimesheetResponse.model_validate(ts) for ts in items]

    # ========================================================================
    # Update entry
    # ========================================================================

    async def update_entry(
        self, entry_id: UUID, payload: TimesheetEntryUpdate
    ) -> TimesheetEntryResponse:
        entry = await self._repo.get_entry(entry_id)
        if entry is None:
            raise NotFoundException(f"Запись табеля с id={entry_id} не найдена.")

        # Load timesheet to check status
        ts = await self._repo.get_by_id(entry.timesheet_id)
        if ts is None:
            raise NotFoundException("Табель не найден.")

        # Business rules for editing
        if ts.status == TimesheetStatus.SUBMITTED:
            raise BusinessRuleException(
                "Нельзя редактировать табель в статусе SUBMITTED."
            )
        if ts.status == TimesheetStatus.APPROVED:
            raise BusinessRuleException(
                "Нельзя редактировать утверждённый табель."
            )
        if ts.status == TimesheetStatus.CLOSED:
            raise BusinessRuleException(
                "Нельзя редактировать закрытый табель."
            )

        updated = await self._repo.update_entry(
            entry,
            attendance_type_id=payload.attendance_type_id,
            hours=payload.hours,
            comment=payload.comment,
        )
        return TimesheetEntryResponse.model_validate(updated)

    # ========================================================================
    # Workflow
    # ========================================================================

    async def _load_and_check(self, ts_id: UUID) -> Timesheet:
        ts = await self._repo.get_by_id(ts_id)
        if ts is None:
            raise NotFoundException(f"Табель с id={ts_id} не найден.")
        return ts

    async def submit(self, ts_id: UUID) -> TimesheetResponse:
        ts = await self._load_and_check(ts_id)
        if ts.status != TimesheetStatus.DRAFT and ts.status != TimesheetStatus.RETURNED:
            raise BusinessRuleException(
                f"Нельзя отправить табель в статусе {ts.status.value}."
            )
        await self._repo.submit(ts)
        return TimesheetResponse.model_validate(ts)

    async def approve(
        self, ts_id: UUID, *, approved_by: UUID
    ) -> TimesheetResponse:
        ts = await self._load_and_check(ts_id)
        if ts.status != TimesheetStatus.SUBMITTED:
            raise BusinessRuleException(
                f"Нельзя утвердить табель в статусе {ts.status.value}."
            )
        await self._repo.approve(ts, approved_by)
        return TimesheetResponse.model_validate(ts)

    async def return_to_revision(self, ts_id: UUID) -> TimesheetResponse:
        ts = await self._load_and_check(ts_id)
        if ts.status != TimesheetStatus.SUBMITTED:
            raise BusinessRuleException(
                f"Нельзя вернуть на доработку табель в статусе {ts.status.value}."
            )
        await self._repo.return_to_revision(ts)
        return TimesheetResponse.model_validate(ts)

    async def close(self, ts_id: UUID) -> TimesheetResponse:
        ts = await self._load_and_check(ts_id)
        if ts.status != TimesheetStatus.APPROVED:
            raise BusinessRuleException(
                f"Нельзя закрыть табель в статусе {ts.status.value}."
            )
        await self._repo.close(ts)
        return TimesheetResponse.model_validate(ts)

    # ========================================================================
    # Matrix view
    # ========================================================================

    async def get_matrix(self, ts_id: UUID) -> TimesheetMatrixResponse:
        ts = await self._repo.get_by_id(ts_id, with_entries=True)
        if ts is None:
            raise NotFoundException(f"Табель с id={ts_id} не найден.")

        period = ts.payroll_period
        dept = ts.department

        import calendar as py_cal
        days_in_month = py_cal.monthrange(period.year, period.month)[1]

        # Group entries by employee
        emp_map: dict[UUID, MatrixEmployeeRow] = {}
        for entry in ts.entries:
            if entry.employee_id not in emp_map:
                emp = entry.employee
                emp_map[entry.employee_id] = MatrixEmployeeRow(
                    employee_id=emp.id,
                    employee_number=emp.employee_number,
                    full_name=emp.full_name,
                    position_name=emp.position.name if emp.position else "",
                    days=[],
                )

        # Build day-by-day matrix
        for emp_id, row in emp_map.items():
            day_dict: dict[int, TimesheetEntry] = {}
            for entry in ts.entries:
                if entry.employee_id == emp_id:
                    day_dict[entry.date.day] = entry

            for day in range(1, days_in_month + 1):
                dt = date(period.year, period.month, day)
                e = day_dict.get(day)
                if e is not None:
                    at = e.attendance_type
                    row.days.append(MatrixDayItem(
                        day=day,
                        date=dt,
                        type_code=at.code if at else "",
                        type_name=at.name if at else "",
                        hours=e.hours,
                        color=at.color if at else "",
                        comment=e.comment,
                    ))
                else:
                    row.days.append(MatrixDayItem(
                        day=day,
                        date=dt,
                        type_code="",
                        type_name="Нет данных",
                        hours=0,
                        color="#EEEEEE",
                    ))

        return TimesheetMatrixResponse(
            timesheet_id=ts.id,
            year=period.year,
            month=period.month,
            department_name=dept.name if dept else "",
            status=ts.status,
            total_employees=len(emp_map),
            total_days=days_in_month,
            employees=list(emp_map.values()),
        )

    # ========================================================================
    # Summary
    # ========================================================================

    async def calculate_summary(
        self, ts_id: UUID
    ) -> TimesheetSummaryResponse:
        ts = await self._repo.get_by_id(ts_id)
        if ts is None:
            raise NotFoundException(f"Табель с id={ts_id} не найден.")
        raw = await self._repo.calculate_summary(ts_id)
        return TimesheetSummaryResponse(**raw)

    # ========================================================================
    # Helpers
    # ========================================================================

    async def _get_detail(self, ts_id: UUID) -> TimesheetDetailResponse:
        ts = await self._repo.get_by_id(ts_id, with_entries=True)
        if ts is None:
            raise NotFoundException(f"Табель с id={ts_id} не найден.")
        return TimesheetDetailResponse(
            id=ts.id,
            payroll_period_id=ts.payroll_period_id,
            department_id=ts.department_id,
            status=ts.status,
            created_by=ts.created_by,
            approved_by=ts.approved_by,
            created_at=ts.created_at,
            updated_at=ts.updated_at,
            approved_at=ts.approved_at,
            entries=[
                TimesheetEntryResponse.model_validate(e) for e in ts.entries
            ],
        )
