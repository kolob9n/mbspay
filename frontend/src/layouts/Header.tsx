import { AppBar, Toolbar, Typography, Box, Chip, IconButton, Avatar, Menu, MenuItem, Divider } from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore, usePeriodStore } from "../../store";

export default function Header() {
  const { user, logout } = useAuthStore();
  const { currentPeriod } = usePeriodStore();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <AppBar position="sticky" sx={{ zIndex: 1201 }}>
      <Toolbar>
        <Typography variant="h6" sx={{ fontWeight: 700, mr: 3 }}>MBS Payroll</Typography>
        {currentPeriod && (
          <Chip label={`${currentPeriod.year}-${String(currentPeriod.month).padStart(2, "0")}`}
            color="secondary" size="small" sx={{ mr: "auto" }} />
        )}
        <Box sx={{ ml: "auto", display: "flex", alignItems: "center", gap: 1 }}>
          <Chip label={user?.role?.name || ""} size="small" variant="outlined" sx={{ color: "white", borderColor: "rgba(255,255,255,0.5)" }} />
          <Typography variant="body2">{user?.full_name}</Typography>
          <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}><Avatar sx={{ width: 32, height: 32, bgcolor: "secondary.main" }}>{user?.full_name?.[0]}</Avatar></IconButton>
          <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={() => setAnchorEl(null)}>
            <MenuItem disabled><Typography variant="body2">{user?.full_name}</Typography></MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>Выйти</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
