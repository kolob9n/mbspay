import { Box, Card, TextField, Button, Typography, Alert } from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store";
import apiClient from "../api/client";

export default function LoginPage() {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login: doLogin } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError("");
    try {
      const { data } = await apiClient.post("/security/login", { login, password });
      const resp = data.data;
      doLogin(resp.access_token, resp.refresh_token, { id: "", login, full_name: login, role: { code: "", name: "", permissions: [] }, permissions: [] });
      const me = await apiClient.get("/security/me");
      if (me.data?.data) doLogin(resp.access_token, resp.refresh_token, me.data.data.user);
      navigate("/");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || "Ошибка входа";
      setError(msg);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "#f5f5f5" }}>
      <Card sx={{ p: 4, width: 400 }}>
        <Typography variant="h5" sx={{ mb: 3, textAlign: "center" }}>MBS Payroll</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <form onSubmit={handleSubmit}>
          <TextField fullWidth label="Логин" value={login} onChange={(e) => setLogin(e.target.value)} sx={{ mb: 2 }} />
          <TextField fullWidth label="Пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} sx={{ mb: 3 }} />
          <Button fullWidth variant="contained" type="submit" size="large">Войти</Button>
        </form>
      </Card>
    </Box>
  );
}
