import { PageShell } from "../../components/PageShell";
import AppTable from "../../components/AppTable";
import { GridColDef } from "@mui/x-data-grid";
import { useQuery } from "@tanstack/react-query";
import apiClient from "../../api/client";
import { ApiResponse } from "../../types";

const columns: GridColDef[] = [
  { field: "employee_number", headerName: "Таб. №", width: 100 },
  { field: "full_name", headerName: "ФИО", width: 250 },
  { field: "is_active", headerName: "Активен", width: 100, type: "boolean" },
];

export default function EmployeesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["employees"],
    queryFn: () => apiClient.get<ApiResponse<{ items: unknown[] }>>("/employees"),
  });
  const rows = data?.data?.data?.items?.map((e: any) => ({ id: e.id, ...e })) || [];
  return <PageShell title="Сотрудники"><AppTable rows={rows} columns={columns} loading={isLoading} /></PageShell>;
}
