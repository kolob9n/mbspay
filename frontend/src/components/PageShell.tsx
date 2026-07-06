import { Box, Typography, Button, Paper } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";

interface PageShellProps { title: string; onAdd?: () => void; addLabel?: string; children: React.ReactNode; }
export function PageShell({ title, onAdd, addLabel, children }: PageShellProps) {
  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Typography variant="h5">{title}</Typography>
        {onAdd && <Button variant="contained" startIcon={<AddIcon />} onClick={onAdd}>{addLabel || "Добавить"}</Button>}
      </Box>
      <Paper sx={{ p: 2 }}>{children}</Paper>
    </Box>
  );
}
