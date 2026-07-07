import { Box, Typography } from "@mui/material";

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        flexShrink: 0,
        px: 3,
        py: 1.5,
        bgcolor: "#fff",
        borderTop: "1px solid",
        borderColor: "divider",
        textAlign: "center",
      }}
    >
      <Typography variant="caption" color="text.secondary">
        MBS Payroll © {new Date().getFullYear()}
      </Typography>
    </Box>
  );
}
