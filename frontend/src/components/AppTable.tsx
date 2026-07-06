import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { Paper } from "@mui/material";

interface AppTableProps { rows: unknown[]; columns: GridColDef[]; loading?: boolean; height?: number; }
export default function AppTable({ rows, columns, loading, height = 500 }: AppTableProps) {
  return (
    <Paper>
      <DataGrid rows={rows} columns={columns} loading={loading}
        sx={{ height, border: 0 }}
        initialState={{ pagination: { paginationModel: { pageSize: 20 } } }}
        pageSizeOptions={[10, 20, 50]} disableRowSelectionOnClick />
    </Paper>
  );
}
