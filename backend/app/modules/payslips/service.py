"""Payslip service — generation, PDF, ZIP archive."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payslips.repository import PayslipRepository
from app.modules.payslips.models import LineType, PayslipStatus
from app.modules.payslips.schemas import PayslipDetailResponse, PayslipItemResponse, PayslipResponse
from app.modules.payroll.models import PayrollResult
from app.modules.payroll.repository import PayrollRepository
from app.shared.exceptions import BusinessRuleException, NotFoundException


class PayslipService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PayslipRepository(session)
        self._payroll_repo = PayrollRepository(session)

    async def generate_all(self, payroll_run_id: UUID, *, generated_by: UUID | None = None) -> list[PayslipResponse]:
        run = await self._payroll_repo.get_by_id(payroll_run_id, with_results=True)
        if run is None: raise NotFoundException("PayrollRun не найден.")
        results = await self._payroll_repo.get_results(payroll_run_id)
        payslips: list[PayslipResponse] = []
        for r in results:
            ps = await self._generate_from_result(r, run.payroll_period_id, generated_by)
            payslips.append(ps)
        return payslips

    async def generate_employee(self, payroll_run_id: UUID, employee_id: UUID, *, generated_by: UUID | None = None) -> PayslipResponse:
        run = await self._payroll_repo.get_by_id(payroll_run_id)
        if run is None: raise NotFoundException("PayrollRun не найден.")
        result = await self._payroll_repo.get_employee_result(payroll_run_id, employee_id)
        if result is None: raise NotFoundException("Результат PayrollResult не найден.")
        return await self._generate_from_result(result, run.payroll_period_id, generated_by)

    async def _generate_from_result(self, r: PayrollResult, payroll_period_id: UUID, generated_by: UUID | None) -> PayslipResponse:
        emp = r.employee
        number = f"PS-{emp.employee_number if emp else 'EMP'}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        now = datetime.now(timezone.utc)

        ps = await self._repo.create(
            employee_id=r.employee_id,
            payroll_run_id=r.payroll_run_id,
            payroll_period_id=payroll_period_id,
            number=number,
            status=PayslipStatus.GENERATED,
            generated_at=now,
            generated_by=generated_by,
        )

        snapshot = r.formula_snapshot or {}
        formulas = snapshot.get("formulas", {}) if isinstance(snapshot, dict) else {}

        item_defs = [
            (LineType.BASE, "Базовая часть", formulas.get("BASE_SALARY"), r.base_salary, 10),
            (LineType.KPI, "KPI (премия)", formulas.get("KPI"), r.kpi, 20),
            (LineType.OVERTIME, "Сверхурочные", None, r.overtime, 30),
            (LineType.BONUS, "Премия", None, r.bonus, 40),
            (LineType.PENALTY, "Штрафы", None, r.penalty, 50),
            (LineType.PAYMENT, "Выплачено", None, r.paid, 60),
            (LineType.TOTAL, "ИТОГО к выдаче", None, r.balance, 100),
        ]
        items_data = [
            {"line_type": lt, "title": title, "formula": form, "amount": amt, "sort_order": sort}
            for lt, title, form, amt, sort in item_defs
            if amt != 0 or lt == LineType.TOTAL
        ]
        await self._repo.create_items(ps.id, items_data)
        return await self._get_detail(ps.id)

    async def get_by_id(self, ps_id: UUID) -> PayslipDetailResponse:
        return await self._get_detail(ps_id)

    async def get_all(
        self, *, period_id: UUID | None = None, employee_id: UUID | None = None,
        status: PayslipStatus | None = None, page: int = 1, size: int = 20
    ) -> list[PayslipResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_all(payroll_period_id=period_id, employee_id=employee_id, status=status, offset=offset, limit=size)
        return [PayslipResponse.model_validate(ps) for ps in items]

    async def get_by_employee(self, employee_id: UUID, page: int = 1, size: int = 100) -> list[PayslipResponse]:
        offset = (page - 1) * size
        items, _ = await self._repo.get_by_employee(employee_id, offset=offset, limit=size)
        return [PayslipResponse.model_validate(ps) for ps in items]

    async def generate_html(self, ps_id: UUID) -> str:
        detail = await self._get_detail(ps_id)
        items_rows = "\n".join(
            f"<tr><td>{i.title}</td><td style='text-align:right'>{float(i.amount):,.2f} &#8381;</td></tr>"
            for i in detail.items if i.line_type != LineType.TOTAL
        )
        total = next((i for i in detail.items if i.line_type == LineType.TOTAL), None)
        gen_date = detail.generated_at.strftime("%d.%m.%Y") if detail.generated_at else "—"
        acc = float(detail.total_accrued)
        ded = float(detail.total_deducted)
        pd = float(detail.total_paid)
        tp = float(detail.to_pay)

        return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Расчётный листок</title>
<style>
  body{{font-family:Arial,sans-serif;margin:40px;font-size:14px}}
  .header{{text-align:center;margin-bottom:20px}}
  .header h2{{margin:0;color:#1565c0}} .header h3{{margin:4px 0}}
  .info{{margin-bottom:20px}} .info p{{margin:2px 0}}
  table{{width:100%;border-collapse:collapse;margin-top:20px}}
  th,td{{border:1px solid #ccc;padding:8px 12px}}
  th{{background:#1565c0;color:white;text-align:left}}
  .amt{{text-align:right}}
  .total{{font-weight:bold;font-size:16px;background:#e3f2fd}}
  .summary{{margin-top:30px;width:300px;float:right}}
  .summary td{{padding:4px 8px;border:none}}
  .summary td:last-child{{text-align:right;font-weight:bold}}
  .footer{{margin-top:80px;text-align:center;color:#888;font-size:12px;clear:both}}
  .qr{{text-align:right;font-size:10px;color:#999}}
</style></head><body>
<div class='header'>
  <h2>MBS Payroll</h2>
  <h3>Расчётный листок № {detail.number}</h3>
</div>
<div class='info'>
  <p><strong>Сотрудник:</strong> {detail.employee_name} (таб. № {detail.employee_number})</p>
  <p><strong>Подразделение:</strong> {detail.department_name} | <strong>Должность:</strong> {detail.position_name}</p>
  <p><strong>Период:</strong> {detail.period_label} | <strong>Дата:</strong> {gen_date} | <strong>Версия:</strong> v{detail.run_version}</p>
</div>
<table>
  <tr><th>Вид начисления / удержания</th><th class='amt'>Сумма</th></tr>
  {items_rows}
  <tr class='total'><td>К ВЫДАЧЕ</td><td class='amt'>{tp:,.2f} &#8381;</td></tr>
</table>
<table class='summary'>
  <tr><td>Начислено:</td><td>{acc:,.2f} &#8381;</td></tr>
  <tr><td>Удержано:</td><td>{ded:,.2f} &#8381;</td></tr>
  <tr><td>Выплачено:</td><td>{pd:,.2f} &#8381;</td></tr>
  <tr style='font-size:18px'><td><strong>К выдаче:</strong></td><td><strong>{tp:,.2f} &#8381;</strong></td></tr>
</table>
<div class='qr'>ID: {detail.id}</div>
<div class='footer'><p>Документ сформирован автоматически. Подписи не требуются.</p></div>
</body></html>"""

    async def _get_detail(self, ps_id: UUID) -> PayslipDetailResponse:
        ps = await self._repo.get_by_id(ps_id)
        if ps is None: raise NotFoundException("Расчётный листок не найден.")
        emp = ps.employee
        run = ps.payroll_run
        period = run.payroll_period if run else None
        accrued = sum((i.amount for i in ps.items if i.line_type not in (LineType.PAYMENT, LineType.TOTAL, LineType.PENALTY)), Decimal("0"))
        deducted = sum((i.amount for i in ps.items if i.line_type in (LineType.PENALTY,)), Decimal("0"))
        paid = sum((i.amount for i in ps.items if i.line_type == LineType.PAYMENT), Decimal("0"))
        total_item = next((i for i in ps.items if i.line_type == LineType.TOTAL), None)
        to_pay = total_item.amount if total_item else Decimal("0")
        return PayslipDetailResponse(
            id=ps.id, employee_id=ps.employee_id, payroll_run_id=ps.payroll_run_id,
            payroll_period_id=ps.payroll_period_id, number=ps.number, status=ps.status,
            generated_at=ps.generated_at, generated_by=ps.generated_by, created_at=ps.created_at,
            items=[PayslipItemResponse.model_validate(i) for i in ps.items],
            employee_name=emp.full_name if emp else "", employee_number=emp.employee_number if emp else "",
            department_name=emp.department.name if emp and emp.department else "",
            position_name=emp.position.name if emp and emp.position else "",
            period_label=period.period_label if period else "",
            run_version=run.version if run else 1,
            total_accrued=accrued, total_deducted=deducted, total_paid=paid, to_pay=to_pay,
        )
