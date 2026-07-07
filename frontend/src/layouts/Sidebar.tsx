import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import DashboardIcon from "@mui/icons-material/Dashboard";
import PeopleIcon from "@mui/icons-material/People";
import BusinessIcon from "@mui/icons-material/Business";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import ScheduleIcon from "@mui/icons-material/Schedule";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import PaymentsIcon from "@mui/icons-material/Payments";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import SettingsIcon from "@mui/icons-material/Settings";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import { useAuthStore } from "../store";

export const DRAWER_WIDTH = 260;

interface MenuItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  permission?: string;
}

const ALL_ITEMS: MenuItem[] = [
  { label: "Дашборд", path: "/", icon: <DashboardIcon /> },
  { label: "Рабочее место", path: "/payroll-workspace", icon: <AccessTimeIcon /> },
  { label: "Сотрудники", path: "/employees", icon: <PeopleIcon />, permission: "EMPLOYEES_VIEW" },
  { label: "Подразделения", path: "/departments", icon: <BusinessIcon /> },
  { label: "Календарь", path: "/calendar", icon: <CalendarMonthIcon /> },
  { label: "Табели", path: "/timesheets", icon: <ScheduleIcon />, permission: "TIMESHEET_VIEW" },
  { label: "KPI", path: "/kpi", icon: <TrendingUpIcon /> },
  { label: "Выплаты", path: "/payments", icon: <PaymentsIcon />, permission: "PAYMENT_CREATE" },
  { label: "Расчёт зарплаты", path: "/payroll", icon: <AccountBalanceIcon />, permission: "PAYROLL_CALCULATE" },
  { label: "Расчётные листки", path: "/payslips", icon: <ReceiptLongIcon /> },
  { label: "Настройки", path: "/settings", icon: <SettingsIcon />, permission: "SETTINGS_EDIT" },
];

export default function Sidebar() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const permissions = user?.permissions || [];

  const visibleItems = ALL_ITEMS.filter((item) => !item.permission || permissions.includes(item.permission));

  const isSelected = (path: string) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: DRAWER_WIDTH,
          position: "relative",
          boxSizing: "border-box",
          border: 0,
          bgcolor: "#3147b7",
          color: "#fff",
          overflowX: "hidden",
        },
      }}
    >
      <Toolbar sx={{ minHeight: "64px !important", px: 2 }}>
        <Typography variant="h6" fontWeight={700} noWrap>
          MBS Payroll
        </Typography>
      </Toolbar>

      <Box sx={{ px: 1.5, py: 1 }}>
        <List disablePadding>
          {visibleItems.map((item) => (
            <ListItemButton
              key={item.path}
              selected={isSelected(item.path)}
              onClick={() => navigate(item.path)}
              sx={{
                mb: 0.5,
                borderRadius: 1.5,
                color: "rgba(255,255,255,0.9)",
                "& .MuiListItemIcon-root": {
                  color: "inherit",
                  minWidth: 40,
                },
                "&.Mui-selected": {
                  bgcolor: "rgba(255,255,255,0.18)",
                  color: "#fff",
                },
                "&.Mui-selected:hover": {
                  bgcolor: "rgba(255,255,255,0.24)",
                },
                "&:hover": {
                  bgcolor: "rgba(255,255,255,0.12)",
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{ fontSize: 14, fontWeight: 500 }}
              />
            </ListItemButton>
          ))}
        </List>
      </Box>
    </Drawer>
  );
}
