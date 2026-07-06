import { Chip } from "@mui/material";

const statusColors: Record<string, "default" | "primary" | "success" | "warning" | "error"> = {
  DRAFT: "default", OPEN: "primary", SUBMITTED: "warning", APPROVED: "success", CLOSED: "default",
  POSTED: "success", CANCELLED: "error", CALCULATED: "info", RETURNED: "warning",
};

export default function AppStatusChip({ status }: { status: string }) {
  return <Chip label={status} color={statusColors[status] || "default"} size="small" />;
}
