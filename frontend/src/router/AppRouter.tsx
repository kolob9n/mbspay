import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import LoginPage from "../pages/LoginPage";
import DashboardPage from "../pages/DashboardPage";
import { useAuthStore } from "../store";
import EmployeesPage from "../modules/employees/EmployeesPage";
import DepartmentsPage from "../modules/departments/DepartmentsPage";
import CalendarPage from "../modules/calendar/CalendarPage";
import TimesheetsPage from "../modules/timetables/TimesheetsPage";
import KpiPage from "../modules/kpi/KpiPage";
import PaymentsPage from "../modules/payments/PaymentsPage";
import PayrollPage from "../modules/payroll/PayrollPage";
import PayrollWorkspacePage from "../modules/payroll-workspace/PayrollWorkspacePage";
import PayslipsListPage from "../modules/payslips/PayslipsListPage";
import PayslipDetailPage from "../modules/payslips/PayslipDetailPage";
import SettingsPage from "../modules/settings/SettingsPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
          <Route index element={<DashboardPage />} />
          <Route path="employees" element={<EmployeesPage />} />
          <Route path="departments" element={<DepartmentsPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="timesheets" element={<TimesheetsPage />} />
          <Route path="kpi" element={<KpiPage />} />
          <Route path="payments" element={<PaymentsPage />} />
          <Route path="payroll" element={<PayrollPage />} />
          <Route path="payroll-workspace" element={<PayrollWorkspacePage />} />
          <Route path="payslips" element={<PayslipsListPage />} />
          <Route path="payslips/:id" element={<PayslipDetailPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}
