import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Chip, Button } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import apiClient from "../../api/client";
import { ApiResponse } from "../../types";
import { PageShell } from "../../components/PageShell";

interface PayslipItem {
  id: string; line_type: string; title: string; formula: string | null;
  amount: number; sort_order: number;
}
interface PayslipDetail {
  id: string; number: string; employee_name: string; employee_number: string;
  department_name: string; position_name: string; period_label: string;
  generated_at: string; run_version: number;
  total_accrued: number; total_deducted: number; total_paid: number; to_pay: number;
  items: PayslipItem[];
}

export default function PayslipDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["payslip", id],
    queryFn: () => apiClient.get<ApiResponse<PayslipDetail>>(`/payslips/${id}`),
    enabled: !!id,
  });

  const detail = data?.data?.data;
  if (isLoading) return <PageShell title="Загрузка..."><></></PageShell>;
  if (!detail) return <PageShell title="Не найдено"><></></PageShell>;

  const accruals = detail.items.filter((i) => !["PAYMENT", "TOTAL", "PENALTY"].includes(i.line_type));
  const deductions = detail.items.filter((i) => i.line_type === "PENALTY");
  const payments = detail.items.filter((i) => i.line_type === "PAYMENT");

  return (
    <PageShell title={`Расчётный листок № ${detail.number}`}>
      <Box sx={{ mb: 3, display: "flex", gap: 2 }}>
        <Button variant="outlined" onClick={() => navigate("/payslips")}>← К списку</Button>
        <Button variant="contained" component="a" href={`/api/v1/payslips/${id}/pdf`} target="_blank">🖨 Печать</Button>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6">{detail.employee_name} (таб. № {detail.employee_number})</Typography>
        <Typography variant="body2">Подразделение: {detail.department_name} | Должность: {detail.position_name}</Typography>
        <Typography variant="body2">Период: {detail.period_label} | Дата: {detail.generated_at ? new Date(detail.generated_at).toLocaleDateString("ru-RU") : "—"} | Версия: v{detail.run_version}</Typography>
      </Paper>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Начисления</Typography>
        <Table size="small">
          <TableHead><TableRow><TableCell>Вид</TableCell><TableCell align="right">Сумма</TableCell></TableRow></TableHead>
          <TableBody>
            {accruals.map((i) => (
              <TableRow key={i.id}><TableCell>{i.title}</TableCell><TableCell align="right">{i.amount.toLocaleString("ru-RU")} ₽</TableCell></TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {deductions.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Удержания</Typography>
          <Table size="small">
            <TableHead><TableRow><TableCell>Вид</TableCell><TableCell align="right">Сумма</TableCell></TableRow></TableHead>
            <TableBody>
              {deductions.map((i) => (
                <TableRow key={i.id}><TableCell>{i.title}</TableCell><TableCell align="right">{i.amount.toLocaleString("ru-RU")} ₽</TableCell></TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Итог</Typography>
        <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          <Box><Typography variant="body2">Начислено</Typography><Typography variant="h6">{detail.total_accrued.toLocaleString("ru-RU")} ₽</Typography></Box>
          <Box><Typography variant="body2">Удержано</Typography><Typography variant="h6">{detail.total_deducted.toLocaleString("ru-RU")} ₽</Typography></Box>
          <Box><Typography variant="body2">Выплачено</Typography><Typography variant="h6">{detail.total_paid.toLocaleString("ru-RU")} ₽</Typography></Box>
          <Box><Typography variant="body2" color="primary">К выдаче</Typography><Typography variant="h4" color="primary">{detail.to_pay.toLocaleString("ru-RU")} ₽</Typography></Box>
        </Box>
      </Paper>
    </PageShell>
  );
}
