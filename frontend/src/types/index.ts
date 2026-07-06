export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PayrollPeriod {
  id: string;
  year: number;
  month: number;
  status: string;
  period_label?: string;
}

export interface Employee {
  id: string;
  employee_number: string;
  full_name: string;
  last_name: string;
  first_name: string;
  department_id: string;
  position_id: string;
  is_active: boolean;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  is_active: boolean;
}

export interface Position {
  id: string;
  name: string;
  code: string;
  is_active: boolean;
}

export interface CalendarDay {
  id: string;
  date: string;
  day_type: string;
  is_working_day: boolean;
  working_hours: number;
}

export interface TimesheetEntry {
  id: string;
  employee_id: string;
  date: string;
  attendance_type_id: string;
  hours: number;
  comment?: string;
}

export interface KpiIndicator {
  id: string;
  code: string;
  name: string;
  formula_id: string;
  weight: number;
  is_active: boolean;
}

export interface Payment {
  id: string;
  number: string;
  date: string;
  payroll_period_id: string;
  status: string;
  total_amount: number;
}

export interface PayrollRun {
  id: string;
  number: string;
  payroll_period_id: string;
  status: string;
  version: number;
  calculation_date?: string;
}

export interface UserProfile {
  id: string;
  login: string;
  full_name: string;
  role: { code: string; name: string; permissions: { code: string }[] };
  permissions: string[];
}
