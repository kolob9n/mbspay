import { Avatar, Box, Chip, Divider, IconButton, Menu, MenuItem, Typography } from "@mui/material";
import { MouseEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore, usePeriodStore } from "../store";

export default function Header() {
  const { user, logout } = useAuthStore();
  const { currentPeriod } = usePeriodStore();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleMenuOpen = (event: MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <Box
      component="header"
      sx={{
        height: 64,
        flexShrink: 0,
        display: "flex",
        alignItems: "center",
        gap: 2,
        px: 3,
        bgcolor: "#fff",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Typography variant="h6" fontWeight={700} noWrap>
        MBS Payroll
      </Typography>

      <Box sx={{ flexGrow: 1 }} />

      {currentPeriod && (
        <Chip
          size="small"
          label={`${currentPeriod.month}.${currentPeriod.year}`}
          color="primary"
          variant="outlined"
        />
      )}

      <Typography variant="body2" color="text.secondary" noWrap>
        {user?.full_name || user?.login || "Admin"}
      </Typography>

      <IconButton onClick={handleMenuOpen} size="small">
        <Avatar sx={{ width: 34, height: 34 }}>
          {(user?.full_name || user?.login || "A")[0]}
        </Avatar>
      </IconButton>

      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2">
            {user?.full_name || "Admin"}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {user?.login}
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={handleLogout}>Выйти</MenuItem>
      </Menu>
    </Box>
  );
}
