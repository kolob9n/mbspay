"""Payment Import Service — extensible Excel import layer.

Design:
- Importer reads the file, extracts rows
- RowMapper maps raw rows → PaymentImportRow
- Validator checks business rules
- Creator builds Payment document + items
- Posting creates ledger entries

This separation allows adding new formats (1C exports, CSV, etc.)
without changing the core import logic.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.repository import EmployeeRepository
from app.modules.payments.models import PaymentStatus, PaymentType
from app.modules.payments.repository import PaymentRepository
from app.modules.payments.schemas import PaymentImportResult
from app.shared.exceptions import BusinessRuleException


class PaymentImportService:
    """Orchestrates payment import from external files.

    Usage::

        service = PaymentImportService(session)
        result = await service.import_file(file, payroll_period_id)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._payment_repo = PaymentRepository(session)
        self._emp_repo = EmployeeRepository(session)

    async def import_file(
        self,
        *,
        file: UploadFile,
        payroll_period_id: UUID,
    ) -> PaymentImportResult:
        """Main entry point: read file → create Payment + post."""

        # 1. Read raw data
        try:
            raw_rows = await self._read_excel(file)
        except Exception as e:
            raise BusinessRuleException(f"Ошибка чтения файла: {e}")

        if not raw_rows:
            raise BusinessRuleException("Файл не содержит данных.")

        # 2. Map to employee
        items_data: list[dict] = []
        errors: list[str] = []
        row_idx = 0

        for row in raw_rows:
            row_idx += 1
            emp = None

            # Try employee_number first, then full name
            emp_number = row.get("employee_number") or row.get("Табельный номер") or row.get("табельный номер")
            emp_name = row.get("employee_name") or row.get("ФИО") or row.get("фио")
            amount_raw = row.get("amount") or row.get("Сумма") or row.get("сумма")

            if emp_number:
                emp = await self._emp_repo.get_by_employee_number(str(emp_number))

            if emp is None and emp_name:
                # Search by full name (brute-force — acceptable for small imports)
                all_emps, _ = await self._emp_repo.get_all(limit=10000)
                name_lower = str(emp_name).strip().lower()
                for e in all_emps:
                    if e.full_name.lower() == name_lower:
                        emp = e
                        break

            if emp is None:
                identifier = emp_number or emp_name or f"строка {row_idx}"
                errors.append(f"Сотрудник не найден: {identifier}")
                continue

            try:
                amount = Decimal(str(amount_raw))
            except Exception:
                errors.append(f"Некорректная сумма в строке {row_idx}: {amount_raw}")
                continue

            if amount <= 0:
                errors.append(f"Сумма должна быть положительной (строка {row_idx})")
                continue

            items_data.append({
                "employee_id": emp.id,
                "amount": amount,
                "payment_type": PaymentType.CARD,
            })

        if not items_data:
            raise BusinessRuleException(
                "Не удалось импортировать ни одной строки. "
                + ("; ".join(errors) if errors else "")
            )

        # 3. Create Payment document
        now = date.today()
        doc_number = f"IMP-{now.strftime('%Y%m%d')}-{datetime.now(timezone.utc).strftime('%H%M%S')}"

        payment = await self._payment_repo.create(
            number=doc_number,
            date=now,
            payroll_period_id=payroll_period_id,
            comment=f"Импорт из файла: {file.filename}",
        )

        await self._payment_repo.create_items(payment.id, items_data)

        # 4. Post → creates ledger entries
        from app.modules.payroll_ledger.repository import PayrollLedgerRepository
        from app.modules.payroll_ledger.models import DocumentType, OperationType

        ledger_repo = PayrollLedgerRepository(self._session)
        for item_data in items_data:
            await ledger_repo.create_entry(
                employee_id=UUID(str(item_data["employee_id"])),
                payroll_period_id=payroll_period_id,
                document_type=DocumentType.IMPORT,
                document_id=payment.id,
                operation_type=OperationType.PAYMENT,
                amount=item_data["amount"],
                operation_date=datetime.now(timezone.utc),
            )

        payment.status = PaymentStatus.POSTED
        await self._session.flush()

        return PaymentImportResult(
            document_id=payment.id,
            rows_imported=len(items_data),
            rows_skipped=row_idx - len(items_data),
            errors=errors,
        )

    # ---- Private -----------------------------------------------------------

    async def _read_excel(self, file: UploadFile) -> list[dict]:
        """Read .xlsx file and return list of row dicts."""
        try:
            import openpyxl
        except ImportError:
            raise BusinessRuleException(
                "Для импорта Excel необходим пакет openpyxl. "
                "Установите: pip install openpyxl"
            )

        contents = await file.read()
        wb = openpyxl.load_workbook(BytesIO(contents), read_only=True, data_only=True)
        ws = wb.active
        if ws is None:
            raise BusinessRuleException("Файл не содержит активного листа.")

        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            return []

        # First row = headers
        headers = [str(h).strip() if h else "" for h in rows[0]]
        data_rows = rows[1:]

        result: list[dict] = []
        for row in data_rows:
            row_dict: dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = value
            # Also support positional columns (no headers case)
            if not row_dict:
                if len(row) >= 1:
                    row_dict["employee_number"] = row[0]
                if len(row) >= 2:
                    row_dict["amount"] = row[1]
            result.append(row_dict)

        return result
