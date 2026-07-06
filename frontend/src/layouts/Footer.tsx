import { Box, Typography } from "@mui/material";

export default function Footer() {
  return (
    <Box component="footer" sx={{ py: 1, px: 3, borderTop: 1, borderColor: "divider", textAlign: "center" }}>
      <Typography variant="caption" color="text.secondary">MBS Payroll © {new Date().getFullYear()}</Typography>
    </Box>
  );
}
