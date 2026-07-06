"""Employee repository — database access layer."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.employees.models import Employee, EmploymentType


class EmployeeRepository:
    """All database queries for Employee live here."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- Create ------------------------------------------------------------

    async def create(
        self,
        *,
        employee_number: str,
        last_name: str,
        first_name: str,
        middle_name: str | None,
        department_id: UUID,
        position_id: UUID,
        employment_type: EmploymentType,
        salary: Decimal,
        work_schedule_id: UUID,
        hire_date: date,
    ) -> Employee:
        emp = Employee(
            employee_number=employee_number,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            department_id=department_id,
            position_id=position_id,
            employment_type=employment_type,
            salary=salary,
            work_schedule_id=work_schedule_id,
            hire_date=hire_date,
        )
        self._session.add(emp)
        await self._session.flush()
        return emp

    # ---- Read --------------------------------------------------------------

    async def get_by_id(
        self, emp_id: UUID, *, with_relations: bool = False
    ) -> Employee | None:
        stmt = select(Employee).where(
            Employee.id == emp_id, Employee.is_deleted == False  # noqa: E712
        )
        if with_relations:
            stmt = stmt.options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.work_schedule),
            )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_employee_number(self, number: str) -> Employee | None:
        stmt = select(Employee).where(
            Employee.employee_number == number,
            Employee.is_deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        is_active: bool | None = None,
        department_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Employee], int]:
        base = select(Employee).where(Employee.is_deleted == False)  # noqa: E712

        if is_active is not None:
            base = base.where(Employee.is_active == is_active)
        if department_id is not None:
            base = base.where(Employee.department_id == department_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        items_stmt = (
            base.options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.work_schedule),
            )
            .order_by(Employee.last_name, Employee.first_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(items_stmt)
        return list(result.unique().scalars().all()), total

    # ---- Update ------------------------------------------------------------

    async def update(self, employee: Employee, **values) -> Employee:
        for key, val in values.items():
            if val is not None:
                setattr(employee, key, val)
        await self._session.flush()
        return employee

    # ---- Dismiss -----------------------------------------------------------

    async def dismiss(self, employee: Employee, dismiss_date: date) -> Employee:
        employee.is_active = False
        employee.dismiss_date = dismiss_date
        await self._session.flush()
        return employee
