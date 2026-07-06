import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from "@mui/material";

interface AppDialogProps { open: boolean; onClose: () => void; title: string; onSave?: () => void; saveLabel?: string; children: React.ReactNode; maxWidth?: "xs" | "sm" | "md" | "lg" | "xl"; }
export default function AppDialog({ open, onClose, title, onSave, saveLabel, children, maxWidth = "sm" }: AppDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth={maxWidth} fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>{children}</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        {onSave && <Button variant="contained" onClick={onSave}>{saveLabel || "Сохранить"}</Button>}
      </DialogActions>
    </Dialog>
  );
}
