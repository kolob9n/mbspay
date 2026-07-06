import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import PeopleIcon from "@mui/icons-material/People";
import BusinessIcon from "@mui/icons-material/Business";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import ScheduleIcon from "@mui/icons-material/Schedule";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import PaymentsIcon from "@mui/icons-material/Payments";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import SettingsIcon from "@mui/icons-material/Settings";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import { useAuthStore } from "../../store";

const DRAWER_WIDTH = 240;

interface MenuItem {
  label: string; path: string; icon: JSX.Element; permission?: string;
}

const ALL_ITEMS: MenuItem[] = [
  { label: "Рабочее место", path: "/payroll-workspace", icon: <AccessTimeIcon /> },
  { label: "Сотрудники", path: "/employees", icon: <PeopleIcon />, permission: "EMPLOYEES_VIEW" },
  { label: "Подразделения", path: "/departments", icon: <BusinessIcon /> },
  { label: "Календарь", path: "/calendar", icon: <CalendarMonthIcon /> },
  { label: "Табели", path: "/timesheets", icon: <ScheduleIcon />, permission: "TIMESHEET_VIEW" },
  { label: "KPI", path: "/kpi", icon: <TrendingUpIcon /> },
  { label: "Выплаты", path: "/payments", icon: <PaymentsIcon />, permission: "PAYMENT_CREATE" },
  { label: "Расчёт зарплаты", path: "/payroll", icon: <AccountBalanceIcon />, permission: "PAYROLL_CALCULATE" },
  { label: "Настройки", path: "/settings", icon: <SettingsIcon />, permission: "SETTINGS_EDIT" },
];

export default function Sidebar() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const perms = user?.permissions || [];

  const visible = ALL_ITEMS.filter((it) => !it.permission || perms.includes(it.permission));

  return (
    <Drawer variant="permanent" sx={{ width: DRAWER_WIDTH, flexShrink: 0, "& .MuiDrawer-paper": { width: DRAWER_WIDTH } }}>
      <Toolbar />
      <List sx={{ px: 1 }}>
        {visible.map((item) => (
          <ListItemButton key={item.path} selected={location.pathname.startsWith(item.path)}
            onClick={() => navigate(item.path)} sx={{ borderRadius: 1, mb: 0.5 }}>
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  );
}

export { DRAWER_WIDTH };
