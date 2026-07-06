"""Payslip service — generates employee payslips from PayrollResults."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payroll.repository import PayrollRepository
from app.modules.payroll.schemas import PayslipResponse
from app.shared.exceptions import NotFoundException


class PayslipService:
    """Generate employee payslips from calculated payroll results."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = PayrollRepository(session)

    async def generate(
        self, employee_id: UUID, payroll_run_id: UUID
    ) -> PayslipResponse:
        result = await self._repo.get_employee_result(payroll_run_id, employee_id)
        if result is None:
            # Try finding result across all runs for this employee
            raise NotFoundException(
                f"Результат расчёта для сотрудника {employee_id} "
                f"в запуске {payroll_run_id} не найден."
            )

        emp = result.employee
        run = result.payroll_run
        period = run.payroll_period if run else None

        to_pay = result.total - result.paid

        return PayslipResponse(
            employee_id=employee_id,
            employee_name=emp.full_name if emp else "",
            employee_number=emp.employee_number if emp else "",
            payroll_run_id=payroll_run_id,
            period_label=period.period_label if period else "",
            salary=result.salary,
            worked_days=result.worked_days,
            norm_days=result.norm_days,
            base_salary=result.base_salary,
            kpi=result.kpi,
            bonus=result.bonus,
            penalty=result.penalty,
            overtime=result.overtime,
            paid=result.paid,
            total=result.total,
            balance=result.balance,
            to_pay=to_pay,
        )
