"""Employee service — all business logic for employees."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.departments.repository import DepartmentRepository
from app.modules.departments.schemas import DepartmentResponse
from app.modules.employees.models import Employee
from app.modules.employees.repository import EmployeeRepository
from app.modules.employees.schemas import (
    EmployeeCardResponse,
    EmployeeCreate,
    EmployeeDismiss,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.modules.positions.repository import PositionRepository
from app.modules.positions.schemas import PositionResponse
from app.modules.work_schedules.repository import WorkScheduleRepository
from app.modules.work_schedules.schemas import WorkScheduleResponse
from app.shared.exceptions import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
)


class EmployeeService:
    """Employee domain logic.

    No SQLAlchemy here — only Repository calls and business rules.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = EmployeeRepository(session)
        self._dept_repo = DepartmentRepository(session)
        self._pos_repo = PositionRepository(session)
        self._ws_repo = WorkScheduleRepository(session)

    # ---- Hire --------------------------------------------------------------

    async def hire_employee(
        self, payload: EmployeeCreate
    ) -> EmployeeCardResponse:
        """Onboard a new employee, enforcing all business rules."""

        # Rule: unique employee_number
        existing = await self._repo.get_by_employee_number(payload.employee_number)
        if existing is not None:
            raise ConflictException(
                f"Сотрудник с табельным номером '{payload.employee_number}' уже существует."
            )

        # Rule: referenced entities must exist
        dept = await self._dept_repo.get_by_id(payload.department_id)
        if dept is None:
            raise NotFoundException(
                f"Подразделение с id={payload.department_id} не найдено."
            )
        pos = await self._pos_repo.get_by_id(payload.position_id)
        if pos is None:
            raise NotFoundException(
                f"Должность с id={payload.position_id} не найдена."
            )
        ws_ = await self._ws_repo.get_by_id(payload.work_schedule_id)
        if ws_ is None:
            raise NotFoundException(
                f"График с id={payload.work_schedule_id} не найден."
            )

        emp = await self._repo.create(
            employee_number=payload.employee_number,
            last_name=payload.last_name,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            department_id=payload.department_id,
            position_id=payload.position_id,
            employment_type=payload.employment_type,
            salary=payload.salary,
            work_schedule_id=payload.work_schedule_id,
            hire_date=payload.hire_date,
        )

        # Reload with relations for the card view
        emp_full = await self._repo.get_by_id(emp.id, with_relations=True)
        assert emp_full is not None
        return self._to_card(emp_full)

    # ---- Read --------------------------------------------------------------

    async def get_employee_card(self, emp_id: UUID) -> EmployeeCardResponse:
        emp = await self._repo.get_by_id(emp_id, with_relations=True)
        if emp is None:
            raise NotFoundException(f"Сотрудник с id={emp_id} не найден.")
        return self._to_card(emp)

    async def get_active_employees(
        self,
        *,
        department_id: UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[EmployeeCardResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(
            is_active=True, department_id=department_id, offset=offset, limit=size
        )
        return [self._to_card(e) for e in items]

    async def get_all_employees(
        self,
        *,
        is_active: bool | None = None,
        department_id: UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[EmployeeCardResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(
            is_active=is_active, department_id=department_id, offset=offset, limit=size
        )
        return [self._to_card(e) for e in items]

    # ---- Update ------------------------------------------------------------

    async def update_employee(
        self, emp_id: UUID, payload: EmployeeUpdate
    ) -> EmployeeCardResponse:
        emp = await self._repo.get_by_id(emp_id, with_relations=True)
        if emp is None:
            raise NotFoundException(f"Сотрудник с id={emp_id} не найден.")

        # Validate FK references if provided
        if payload.department_id is not None:
            if await self._dept_repo.get_by_id(payload.department_id) is None:
                raise NotFoundException(
                    f"Подразделение с id={payload.department_id} не найдено."
                )
        if payload.position_id is not None:
            if await self._pos_repo.get_by_id(payload.position_id) is None:
                raise NotFoundException(
                    f"Должность с id={payload.position_id} не найдена."
                )
        if payload.work_schedule_id is not None:
            if await self._ws_repo.get_by_id(payload.work_schedule_id) is None:
                raise NotFoundException(
                    f"График с id={payload.work_schedule_id} не найден."
                )

        updated = await self._repo.update(
            emp,
            last_name=payload.last_name,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            department_id=payload.department_id,
            position_id=payload.position_id,
            employment_type=payload.employment_type,
            salary=payload.salary,
            work_schedule_id=payload.work_schedule_id,
        )
        return self._to_card(updated)

    async def change_department(
        self, emp_id: UUID, new_department_id: UUID
    ) -> EmployeeCardResponse:
        if await self._dept_repo.get_by_id(new_department_id) is None:
            raise NotFoundException(
                f"Подразделение с id={new_department_id} не найдено."
            )
        emp = await self._repo.get_by_id(emp_id, with_relations=True)
        if emp is None:
            raise NotFoundException(f"Сотрудник с id={emp_id} не найден.")
        updated = await self._repo.update(emp, department_id=new_department_id)
        return self._to_card(updated)

    async def change_salary(
        self, emp_id: UUID, new_salary: Decimal
    ) -> EmployeeCardResponse:
        if new_salary <= 0:
            raise BusinessRuleException("Оклад должен быть положительным.")
        emp = await self._repo.get_by_id(emp_id, with_relations=True)
        if emp is None:
            raise NotFoundException(f"Сотрудник с id={emp_id} не найден.")
        updated = await self._repo.update(emp, salary=new_salary)
        return self._to_card(updated)

    # ---- Dismiss -----------------------------------------------------------

    async def dismiss_employee(
        self, emp_id: UUID, payload: EmployeeDismiss
    ) -> EmployeeCardResponse:
        emp = await self._repo.get_by_id(emp_id, with_relations=True)
        if emp is None:
            raise NotFoundException(f"Сотрудник с id={emp_id} не найден.")
        if not emp.is_active:
            raise BusinessRuleException(
                f"Сотрудник {emp.full_name} уже уволен."
            )
        dismissed = await self._repo.dismiss(emp, payload.dismiss_date)
        return self._to_card(dismissed)

    # ---- Helpers -----------------------------------------------------------

    @staticmethod
    def _to_card(emp: Employee) -> EmployeeCardResponse:
        return EmployeeCardResponse(
            id=emp.id,
            employee_number=emp.employee_number,
            last_name=emp.last_name,
            first_name=emp.first_name,
            middle_name=emp.middle_name,
            full_name=emp.full_name,
            department_id=emp.department_id,
            position_id=emp.position_id,
            employment_type=emp.employment_type,
            salary=emp.salary,
            work_schedule_id=emp.work_schedule_id,
            is_active=emp.is_active,
            hire_date=emp.hire_date,
            dismiss_date=emp.dismiss_date,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
            department=(
                DepartmentResponse.model_validate(emp.department)
                if emp.department is not None
                else None
            ),
            position=(
                PositionResponse.model_validate(emp.position)
                if emp.position is not None
                else None
            ),
            work_schedule=(
                WorkScheduleResponse.model_validate(emp.work_schedule)
                if emp.work_schedule is not None
                else None
            ),
        )
