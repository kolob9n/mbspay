import { PageShell } from "../../components/PageShell";
import AppTable from "../../components/AppTable";
import { GridColDef } from "@mui/x-data-grid";
import { useQuery } from "@tanstack/react-query";
import apiClient from "../../api/client";
import { ApiResponse } from "../../types";

const columns: GridColDef[] = [
  { field: "key", headerName: "Ключ", width: 200 },
  { field: "value", headerName: "Значение", width: 200 },
  { field: "value_type", headerName: "Тип", width: 100 },
  { field: "description", headerName: "Описание", width: 300 },
];

export default function SettingsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: () => apiClient.get<ApiResponse<unknown[]>>("/settings"),
  });
  const rows = (data?.data?.data || []).map((e: any) => ({ id: e.id, ...e }));
  return <PageShell title="Настройки системы"><AppTable rows={rows} columns={columns} loading={isLoading} /></PageShell>;
}
