"""Payment service — business logic for payments + ledger integration."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.repository import EmployeeRepository
from app.modules.payments.models import PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.modules.payments.schemas import (
    PaymentCreate,
    PaymentDetailResponse,
    PaymentItemResponse,
    PaymentResponse,
    PaymentUpdate,
)
from app.shared.exceptions import BusinessRuleException, ConflictException, NotFoundException


class PaymentService:
    """Payment document management + ledger posting."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PaymentRepository(session)
        self._emp_repo = EmployeeRepository(session)

    # ========================================================================
    # Create
    # ========================================================================

    async def create(
        self, payload: PaymentCreate, *, created_by: UUID | None = None
    ) -> PaymentDetailResponse:
        existing = await self._repo.get_by_number(payload.number)
        if existing is not None:
            raise ConflictException(
                f"Документ с номером '{payload.number}' уже существует."
            )

        payment = await self._repo.create(
            number=payload.number,
            date=payload.date,
            payroll_period_id=payload.payroll_period_id,
            comment=payload.comment,
            created_by=created_by,
        )

        # Validate employees
        items_data: list[dict] = []
        for item in payload.items:
            emp = await self._emp_repo.get_by_id(item.employee_id)
            if emp is None:
                raise NotFoundException(
                    f"Сотрудник с id={item.employee_id} не найден."
                )
            items_data.append(item.model_dump())

        await self._repo.create_items(payment.id, items_data)
        return await self._get_detail(payment.id)

    # ========================================================================
    # Read
    # ========================================================================

    async def get_all(
        self,
        *,
        status: PaymentStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[PaymentResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(status=status, offset=offset, limit=size)
        result: list[PaymentResponse] = []
        for p in items:
            total = await self._repo.get_total_amount(p.id)
            result.append(
                PaymentResponse(
                    id=p.id,
                    number=p.number,
                    date=p.date,
                    payroll_period_id=p.payroll_period_id,
                    status=p.status,
                    comment=p.comment,
                    created_by=p.created_by,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    total_amount=total,
                )
            )
        return result

    async def get_by_id(self, payment_id: UUID) -> PaymentDetailResponse:
        return await self._get_detail(payment_id)

    # ========================================================================
    # Update (DRAFT only)
    # ========================================================================

    async def update(
        self, payment_id: UUID, payload: PaymentUpdate
    ) -> PaymentDetailResponse:
        payment = await self._repo.get_by_id(payment_id)
        if payment is None:
            raise NotFoundException(f"Документ с id={payment_id} не найден.")

        if payment.status != PaymentStatus.DRAFT:
            raise BusinessRuleException(
                "Редактировать можно только документ в статусе DRAFT."
            )

        await self._repo.update(
            payment, **payload.model_dump(exclude_none=True)
        )
        return await self._get_detail(payment_id)

    # ========================================================================
    # Post (DRAFT → POSTED) — creates ledger entries
    # ========================================================================

    async def post(self, payment_id: UUID) -> PaymentDetailResponse:
        payment = await self._repo.get_by_id(payment_id, with_items=True)
        if payment is None:
            raise NotFoundException(f"Документ с id={payment_id} не найден.")

        if payment.status != PaymentStatus.DRAFT:
            raise BusinessRuleException(
                f"Нельзя провести документ в статусе {payment.status.value}."
            )

        # Create ledger entries
        from app.modules.payroll_ledger.repository import PayrollLedgerRepository
        from app.modules.payroll_ledger.models import DocumentType, OperationType

        ledger_repo = PayrollLedgerRepository(self._session)
        items = await self._repo.get_items(payment_id)

        for item in items:
            await ledger_repo.create_entry(
                employee_id=item.employee_id,
                payroll_period_id=payment.payroll_period_id,
                document_type=DocumentType.PAYMENT,
                document_id=payment.id,
                operation_type=OperationType.PAYMENT,
                amount=item.amount,
                operation_date=datetime.now(timezone.utc),
            )

        payment.status = PaymentStatus.POSTED
        await self._session.flush()
        return await self._get_detail(payment_id)

    # ========================================================================
    # Cancel (POSTED → CANCELLED) — creates reversing entries
    # ========================================================================

    async def cancel(self, payment_id: UUID) -> PaymentDetailResponse:
        payment = await self._repo.get_by_id(payment_id, with_items=True)
        if payment is None:
            raise NotFoundException(f"Документ с id={payment_id} не найден.")

        if payment.status != PaymentStatus.POSTED:
            raise BusinessRuleException(
                f"Нельзя отменить документ в статусе {payment.status.value}."
            )

        # Create reversing ledger entries (CORRECTION with negative amount)
        from app.modules.payroll_ledger.repository import PayrollLedgerRepository
        from app.modules.payroll_ledger.models import DocumentType, OperationType

        ledger_repo = PayrollLedgerRepository(self._session)
        items = await self._repo.get_items(payment_id)

        for item in items:
            await ledger_repo.create_entry(
                employee_id=item.employee_id,
                payroll_period_id=payment.payroll_period_id,
                document_type=DocumentType.PAYMENT,
                document_id=payment.id,
                operation_type=OperationType.CORRECTION,
                amount=-item.amount,  # reversing
                operation_date=datetime.now(timezone.utc),
            )

        payment.status = PaymentStatus.CANCELLED
        await self._session.flush()
        return await self._get_detail(payment_id)

    # ========================================================================
    # Helpers
    # ========================================================================

    async def _get_detail(self, payment_id: UUID) -> PaymentDetailResponse:
        payment = await self._repo.get_by_id(payment_id)
        if payment is None:
            raise NotFoundException(f"Документ с id={payment_id} не найден.")

        items = await self._repo.get_items(payment_id)
        total = await self._repo.get_total_amount(payment_id)

        return PaymentDetailResponse(
            id=payment.id,
            number=payment.number,
            date=payment.date,
            payroll_period_id=payment.payroll_period_id,
            status=payment.status,
            comment=payment.comment,
            created_by=payment.created_by,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            total_amount=total,
            items=[PaymentItemResponse.model_validate(i) for i in items],
        )
