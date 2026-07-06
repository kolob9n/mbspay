import { Container, Typography, Box } from "@mui/material";

export default function HomePage() {
  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 8, textAlign: "center" }}>
        <Typography variant="h3" component="h1" gutterBottom>
          MBS Payroll
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Система расчёта заработной платы
        </Typography>
      </Box>
    </Container>
  );
}
