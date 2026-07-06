import { useState } from "react";
import { Box, TextField, MenuItem, IconButton, Tooltip } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import VisibilityIcon from "@mui/icons-material/Visibility";
import DownloadIcon from "@mui/icons-material/Download";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";
import { ApiResponse } from "../../types";
import { PageShell } from "../../components/PageShell";
import AppStatusChip from "../../components/AppStatusChip";

export default function PayslipsListPage() {
  const navigate = useNavigate();
  const [periodFilter, setPeriodFilter] = useState("");
  const [employeeFilter, setEmployeeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data: periodData } = useQuery({
    queryKey: ["periods-for-filter"],
    queryFn: () => apiClient.get<ApiResponse<{ items: { id: string; year: number; month: number }[] }>>("/periods?size=100"),
  });
  const periods = periodData?.data?.data?.items || [];

  const { data, isLoading } = useQuery({
    queryKey: ["payslips", periodFilter, employeeFilter, statusFilter],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (periodFilter) params.period_id = periodFilter;
      if (employeeFilter) params.employee_id = employeeFilter;
      if (statusFilter) params.status = statusFilter;
      return apiClient.get<ApiResponse<unknown[]>>("/payslips", { params });
    },
  });

  const rows = (data?.data?.data || []).map((ps: any) => ({ id: ps.id, ...ps }));

  const columns: GridColDef[] = [
    { field: "number", headerName: "Номер", width: 220 },
    { field: "status", headerName: "Статус", width: 130, renderCell: (p) => <AppStatusChip status={p.value as string} /> },
    { field: "created_at", headerName: "Дата", width: 170, valueFormatter: (v: string) => v ? new Date(v).toLocaleDateString("ru-RU") : "" },
    { field: "actions", headerName: "", width: 120, sortable: false,
      renderCell: (p) => (
        <Box>
          <Tooltip title="Просмотр"><IconButton size="small" onClick={() => navigate(`/payslips/${p.id}`)}><VisibilityIcon /></IconButton></Tooltip>
          <Tooltip title="Скачать"><IconButton size="small" component="a" href={`/api/v1/payslips/${p.id}/pdf`} target="_blank"><DownloadIcon /></IconButton></Tooltip>
        </Box>
      ),
    },
  ];

  return (
    <PageShell title="Расчётные листки">
      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <TextField select size="small" label="Период" value={periodFilter}
          onChange={(e) => setPeriodFilter(e.target.value)} sx={{ width: 200 }}>
          <MenuItem value="">Все</MenuItem>
          {periods.map((p: any) => (
            <MenuItem key={p.id} value={p.id}>{p.year}-{String(p.month).padStart(2, "0")}</MenuItem>
          ))}
        </TextField>
        <TextField size="small" label="Сотрудник (ID)" value={employeeFilter}
          onChange={(e) => setEmployeeFilter(e.target.value)} sx={{ width: 300 }} />
        <TextField select size="small" label="Статус" value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)} sx={{ width: 180 }}>
          <MenuItem value="">Все</MenuItem>
          <MenuItem value="GENERATED">Сформирован</MenuItem>
          <MenuItem value="SIGNED">Подписан</MenuItem>
          <MenuItem value="ARCHIVED">Архивирован</MenuItem>
        </TextField>
      </Box>
      <DataGrid rows={rows} columns={columns} loading={isLoading}
        sx={{ height: 500, border: 0 }} pageSizeOptions={[10, 20, 50]}
        initialState={{ pagination: { paginationModel: { pageSize: 20 } } }} disableRowSelectionOnClick />
    </PageShell>
  );
}
