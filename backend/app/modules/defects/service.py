"""Defect service — business logic for defect tracking."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.defects.repository import DefectRepository
from app.modules.defects.schemas import (
    DefectCreate,
    DefectEmployeeSummary,
    DefectResponse,
    DefectTypeCreate,
    DefectTypeResponse,
    DefectTypeUpdate,
    DefectUpdate,
)
from app.modules.employees.repository import EmployeeRepository
from app.shared.exceptions import ConflictException, NotFoundException


class DefectService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = DefectRepository(session)
        self._emp_repo = EmployeeRepository(session)

    # ========================================================================
    # DefectType
    # ========================================================================

    async def create_type(self, payload: DefectTypeCreate) -> DefectTypeResponse:
        existing = await self._repo.get_type_by_code(payload.code)
        if existing is not None:
            raise ConflictException(f"Тип брака с кодом '{payload.code}' уже существует.")
        dt = await self._repo.create_type(**payload.model_dump())
        return DefectTypeResponse.model_validate(dt)

    async def get_all_types(self) -> list[DefectTypeResponse]:
        items = await self._repo.get_all_types()
        return [DefectTypeResponse.model_validate(t) for t in items]

    async def update_type(
        self, dt_id: UUID, payload: DefectTypeUpdate
    ) -> DefectTypeResponse:
        dt = await self._repo.get_type_by_id(dt_id)
        if dt is None:
            raise NotFoundException(f"Тип брака с id={dt_id} не найден.")
        updated = await self._repo.update_type(
            dt, **payload.model_dump(exclude_none=True)
        )
        return DefectTypeResponse.model_validate(updated)

    # ========================================================================
    # Defect
    # ========================================================================

    async def create(
        self, payload: DefectCreate, *, created_by: UUID | None = None
    ) -> DefectResponse:
        emp = await self._emp_repo.get_by_id(payload.employee_id)
        if emp is None:
            raise NotFoundException(f"Сотрудник с id={payload.employee_id} не найден.")
        dt = await self._repo.get_type_by_id(payload.defect_type_id)
        if dt is None:
            raise NotFoundException(f"Тип брака с id={payload.defect_type_id} не найден.")
        d = await self._repo.create(
            employee_id=payload.employee_id,
            date=payload.date,
            defect_type_id=payload.defect_type_id,
            description=payload.description,
            created_by=created_by,
        )
        return DefectResponse.model_validate(d)

    async def get_by_employee(
        self, employee_id: UUID, *, page: int = 1, size: int = 100
    ) -> list[DefectResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_by_employee(
            employee_id, offset=offset, limit=size
        )
        return [DefectResponse.model_validate(d) for d in items]

    async def update(
        self, defect_id: UUID, payload: DefectUpdate
    ) -> DefectResponse:
        d = await self._repo.get_by_id(defect_id)
        if d is None:
            raise NotFoundException(f"Запись о браке с id={defect_id} не найдена.")
        updated = await self._repo.update(d, **payload.model_dump(exclude_none=True))
        return DefectResponse.model_validate(updated)

    async def get_employee_summary(
        self, employee_id: UUID, payroll_period_id: UUID
    ) -> DefectEmployeeSummary:
        total = await self._repo.count_by_employee_period(
            employee_id, payroll_period_id
        )
        by_type = await self._repo.count_by_employee_period_by_type(
            employee_id, payroll_period_id
        )
        return DefectEmployeeSummary(
            employee_id=employee_id,
            total_defects=total,
            by_type=by_type,
        )
