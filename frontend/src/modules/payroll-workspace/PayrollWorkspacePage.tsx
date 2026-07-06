import { useState } from "react";
import {
  Box, Typography, Paper, Grid, Card, CardContent, Button, Chip, Alert, LinearProgress,
  Stepper, Step, StepLabel, Dialog, DialogTitle, DialogContent, Select, MenuItem, FormControl, InputLabel, List, ListItem, ListItemIcon, ListItemText
} from "@mui/material";
import WarningIcon from "@mui/icons-material/Warning";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../../api/client";
import { ApiResponse } from "../../types";
import { usePeriodStore } from "../../store";

interface ModuleStatus { calendar: boolean; timesheets: boolean; kpi: boolean; payments: boolean; payroll: boolean; payslips: boolean; closed: boolean; }
interface WorkspaceError { code: string; message: string; module: string; entity_id?: string; }
interface StatusResponse { period_id: string; period_label: string; period_status: string; modules: ModuleStatus; errors: WorkspaceError[]; }
interface KpiStats { total_employees: number; calculated: number; errors: number; }
interface PaymentStats { documents_count: number; total_amount: number; total_employees: number; last_import_date?: string; }
interface PayrollStats { total_accrued: number; total_paid: number; total_balance: number; total_employees: number; run_status?: string; }

const STEPS = [
  { key: "calendar", label: "Производственный календарь" },
  { key: "timesheets", label: "Табели" },
  { key: "kpi", label: "KPI" },
  { key: "payments", label: "Выплаты" },
  { key: "payroll", label: "Расчёт зарплаты" },
  { key: "payslips", label: "Расчётные листы" },
  { key: "closed", label: "Закрытие месяца" },
] as const;

function StatusIcon({ done }: { done: boolean }) {
  return done ? <CheckCircleIcon color="success" /> : <ErrorIcon color="disabled" />;
}

function fmt(n: number) { return new Intl.NumberFormat("ru-RU").format(n); }

export default function PayrollWorkspacePage() {
  const { currentPeriod, setPeriod } = usePeriodStore();
  const queryClient = useQueryClient();
  const [periodDialogOpen, setPeriodDialogOpen] = useState(false);
  const [selectedPeriodId, setSelectedPeriodId] = useState(currentPeriod?.id || "");

  // Fetch periods list
  const { data: periodsData } = useQuery({
    queryKey: ["periods-list"],
    queryFn: () => apiClient.get<ApiResponse<{ items: { id: string; year: number; month: number; status: string }[] }>>("/periods?size=100"),
  });

  const periods = periodsData?.data?.data?.items || [];

  const periodId = currentPeriod?.id || selectedPeriodId;

  // Fetch workspace status
  const { data: statusData, isLoading: statusLoading } = useQuery({
    queryKey: ["workspace-status", periodId],
    queryFn: () => apiClient.get<ApiResponse<StatusResponse>>(`/payroll-workspace/status/${periodId}`),
    enabled: !!periodId,
    refetchInterval: 10_000,
  });

  // Fetch KPI stats
  const { data: kpiData } = useQuery({
    queryKey: ["workspace-kpi", periodId],
    queryFn: () => apiClient.get<ApiResponse<KpiStats>>(`/payroll-workspace/kpi-status/${periodId}`),
    enabled: !!periodId,
  });

  // Fetch Payment stats
  const { data: paymentData } = useQuery({
    queryKey: ["workspace-payment", periodId],
    queryFn: () => apiClient.get<ApiResponse<PaymentStats>>(`/payroll-workspace/payment-status/${periodId}`),
    enabled: !!periodId,
  });

  // Fetch Payroll stats
  const { data: payrollData } = useQuery({
    queryKey: ["workspace-payroll", periodId],
    queryFn: () => apiClient.get<ApiResponse<PayrollStats>>(`/payroll-workspace/payroll-status/${periodId}`),
    enabled: !!periodId,
  });

  const status = statusData?.data?.data;
  const modules = status?.modules;
  const errors = status?.errors || [];
  const kpiStats = kpiData?.data?.data;
  const paymentStats = paymentData?.data?.data;
  const payrollStats = payrollData?.data?.data;

  // Mutations
  const calcKpi = useMutation({
    mutationFn: () => apiClient.post(`/payroll-workspace/calculate-kpi/${periodId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspace-"] }),
  });
  const calcPayroll = useMutation({
    mutationFn: () => apiClient.post(`/payroll-workspace/calculate-payroll/${periodId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspace-"] }),
  });
  const approvePayroll = useMutation({
    mutationFn: () => apiClient.post(`/payroll-workspace/approve-payroll/${periodId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspace-"] }),
  });
  const closePeriod = useMutation({
    mutationFn: () => apiClient.post(`/payroll-workspace/close-period/${periodId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspace-"] }),
  });

  const activeStep = modules ? STEPS.findLastIndex((s) => modules[s.key as keyof ModuleStatus]) : -1;

  return (
    <Box>
      {/* ===== Top bar ===== */}
      <Paper sx={{ p: 2, mb: 3, display: "flex", alignItems: "center", gap: 3 }}>
        <Box>
          <Typography variant="overline" color="text.secondary">Расчётный период</Typography>
          <Typography variant="h5">{status?.period_label || "—"}</Typography>
        </Box>
        <Chip label={status?.period_status || "—"} color="primary" />
        <Box sx={{ ml: "auto" }}>
          <Button variant="outlined" onClick={() => setPeriodDialogOpen(true)}>Сменить период</Button>
        </Box>
      </Paper>

      <Grid container spacing={3}>
        {/* ===== Readiness stepper ===== */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Готовность периода</Typography>
            {statusLoading && <LinearProgress />}
            {modules && (
              <Stepper activeStep={activeStep} alternativeLabel>
                {STEPS.map((step) => (
                  <Step key={step.key} completed={modules[step.key as keyof ModuleStatus]}>
                    <StepLabel StepIconComponent={() => <StatusIcon done={modules[step.key as keyof ModuleStatus]} />}>
                      {step.label}
                    </StepLabel>
                  </Step>
                ))}
              </Stepper>
            )}

            {/* Action buttons */}
            <Box sx={{ mt: 4, display: "flex", gap: 2, flexWrap: "wrap" }}>
              {modules && !modules.kpi && (
                <Button variant="contained" startIcon={<PlayArrowIcon />} onClick={() => calcKpi.mutate()} loading={calcKpi.isPending}>
                  Рассчитать KPI
                </Button>
              )}
              {modules?.kpi && !modules?.payments && (
                <Button variant="outlined" onClick={() => window.location.href = "/payments"}>
                  Импорт выплат
                </Button>
              )}
              {modules?.kpi && modules?.payments && !modules?.payroll && (
                <Button variant="contained" startIcon={<PlayArrowIcon />} onClick={() => calcPayroll.mutate()} loading={calcPayroll.isPending}>
                  Рассчитать зарплату
                </Button>
              )}
              {modules?.payroll && !modules?.payslips && (
                <Button variant="contained" color="success" onClick={() => approvePayroll.mutate()} loading={approvePayroll.isPending}>
                  Утвердить расчет
                </Button>
              )}
              {modules?.payslips && !modules?.closed && (
                <Button variant="contained" color="warning" onClick={() => closePeriod.mutate()} loading={closePeriod.isPending}>
                  Закрыть месяц
                </Button>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* ===== Widgets ===== */}
        <Grid item xs={12} lg={4}>
          <Stack spacing={2}>
            {/* KPI Widget */}
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary">KPI</Typography>
                <Typography variant="body2">Сотрудников: {kpiStats?.total_employees ?? "—"}</Typography>
                <Typography variant="body2">Рассчитано: {kpiStats?.calculated ?? "—"}</Typography>
                <Typography variant="body2">Ошибок: {kpiStats?.errors ?? "—"}</Typography>
              </CardContent>
            </Card>

            {/* Payments Widget */}
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary">Выплаты</Typography>
                <Typography variant="body2">Документов: {paymentStats?.documents_count ?? "—"}</Typography>
                <Typography variant="body2">Сотрудников: {paymentStats?.total_employees ?? "—"}</Typography>
                <Typography variant="h6">{fmt(paymentStats?.total_amount || 0)} ₽</Typography>
              </CardContent>
            </Card>

            {/* Payroll Widget */}
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary">Расчёт зарплаты</Typography>
                <Typography variant="body2">Начислено: {fmt(payrollStats?.total_accrued || 0)} ₽</Typography>
                <Typography variant="body2">Выплачено: {fmt(payrollStats?.total_paid || 0)} ₽</Typography>
                <Typography variant="h6" color="primary">{fmt(payrollStats?.total_balance || 0)} ₽ к выдаче</Typography>
              </CardContent>
            </Card>
          </Stack>
        </Grid>

        {/* ===== Errors ===== */}
        {errors.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2, bgcolor: "#fff3e0" }}>
              <Typography variant="h6" sx={{ mb: 1, display: "flex", alignItems: "center", gap: 1 }}>
                <WarningIcon color="warning" /> Обнаружены проблемы ({errors.length})
              </Typography>
              <List dense>
                {errors.map((e, i) => (
                  <ListItem key={i}>
                    <ListItemIcon><ErrorIcon color="error" fontSize="small" /></ListItemIcon>
                    <ListItemText primary={e.message} secondary={e.module} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Period dialog */}
      <Dialog open={periodDialogOpen} onClose={() => setPeriodDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Выберите период</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel>Период</InputLabel>
            <Select value={selectedPeriodId} label="Период" onChange={(e) => {
              setSelectedPeriodId(e.target.value);
              const p = periods.find((p: { id: string }) => p.id === e.target.value);
              if (p) setPeriod({ id: p.id, year: p.year, month: p.month, status: p.status });
              setPeriodDialogOpen(false);
            }}>
              {periods.map((p: { id: string; year: number; month: number }) => (
                <MenuItem key={p.id} value={p.id}>{p.year}-{String(p.month).padStart(2, "0")}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
      </Dialog>
    </Box>
  );
}

// Inline Stack (simple vertical stack)
function Stack({ children, spacing }: { children: React.ReactNode; spacing: number }) {
  return <Box sx={{ display: "flex", flexDirection: "column", gap: spacing }}>{children}</Box>;
}
