import { Box, Paper, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";
import { ApiResponse, PaginatedResponse, PayrollPeriod } from "../types";

function DashboardWidget({
  title,
  value,
  color,
}: {
  title: string;
  value: string | number;
  color: string;
}) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        minHeight: 120,
        borderRadius: 2,
        border: "1px solid",
        borderColor: "divider",
        borderLeft: `5px solid ${color}`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <Typography variant="body2" color="text.secondary">
        {title}
      </Typography>
      <Typography variant="h4" fontWeight={700}>
        {value}
      </Typography>
    </Paper>
  );
}

export default function DashboardPage() {
  const { data: empData } = useQuery({
    queryKey: ["employees-count"],
    queryFn: () => apiClient.get<ApiResponse<PaginatedResponse<unknown>>>("/employees/?size=1"),
    retry: false,
  });

  const { data: periodData } = useQuery({
    queryKey: ["periods-current"],
    queryFn: () => apiClient.get<ApiResponse<PayrollPeriod>>("/periods/current"),
    retry: false,
  });

  const employeesTotal = empData?.data?.data?.total ?? "—";
  const currentPeriod = periodData?.data?.data;
  const periodLabel = currentPeriod
    ? `${String(currentPeriod.month).padStart(2, "0")}.${currentPeriod.year}`
    : "—";

  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: 1200,
        mx: "auto",
      }}
    >
      <Typography variant="h4" fontWeight={700} sx={{ mb: 3 }}>
        Дашборд
      </Typography>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(2, minmax(0, 1fr))",
            lg: "repeat(4, minmax(0, 1fr))",
          },
          gap: 2.5,
          width: "100%",
        }}
      >
        <DashboardWidget title="Сотрудников" value={employeesTotal} color="#3f51b5" />
        <DashboardWidget title="Активный период" value={periodLabel} color="#ff6d00" />
        <DashboardWidget title="Неутверждено табелей" value="—" color="#9c27b0" />
        <DashboardWidget title="Документов выплат" value="—" color="#4caf50" />
      </Box>
    </Box>
  );
}
