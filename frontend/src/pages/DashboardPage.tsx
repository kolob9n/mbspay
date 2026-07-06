import { Box, Typography, Paper, Grid, CircularProgress } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";
import { ApiResponse } from "../types";

function DashboardWidget({ title, value, color }: { title: string; value: string | number; color: string }) {
  return (
    <Paper sx={{ p: 3, borderLeft: 4, borderColor: color }}>
      <Typography variant="subtitle2" color="text.secondary">{title}</Typography>
      <Typography variant="h4" sx={{ mt: 1 }}>{value}</Typography>
    </Paper>
  );
}

export default function DashboardPage() {
  const { data: empData } = useQuery({ queryKey: ["employees-count"], queryFn: () => apiClient.get<ApiResponse<{ items: unknown[] }>>("/employees?size=1") });
  const { data: periodData } = useQuery({ queryKey: ["periods-current"], queryFn: () => apiClient.get<ApiResponse<unknown>>("/periods/current") });

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3 }}>Дашборд</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} lg={3}>
          <DashboardWidget title="Сотрудников" value={empData?.data?.data?.items?.length ?? "—"} color="#1565c0" />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <DashboardWidget title="Активный период" value={periodData?.data?.data ? "✓" : "—"} color="#ff6f00" />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <DashboardWidget title="Неподтв. табели" value="—" color="#9c27b0" />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <DashboardWidget title="Документов выплат" value="—" color="#4caf50" />
        </Grid>
      </Grid>
    </Box>
  );
}
