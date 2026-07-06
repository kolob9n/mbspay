import { PageShell } from "../../components/PageShell";
import AppTable from "../../components/AppTable";
import { GridColDef } from "@mui/x-data-grid";
import { useQuery } from "@tanstack/react-query";
import apiClient from "../../api/client";
import { ApiResponse } from "../../types";

const columns: GridColDef[] = [
  { field: "code", headerName: "Код", width: 120 },
  { field: "name", headerName: "Название", width: 300 },
  { field: "is_active", headerName: "Активно", width: 100, type: "boolean" },
];

export default function DepartmentsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["departments"],
    queryFn: () => apiClient.get<ApiResponse<unknown[]>>("/departments"),
  });
  const rows = (data?.data?.data || []).map((e: any) => ({ id: e.id, ...e }));
  return <PageShell title="Подразделения"><AppTable rows={rows} columns={columns} loading={isLoading} /></PageShell>;
}
