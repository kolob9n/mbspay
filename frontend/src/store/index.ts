import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: import("../types").UserProfile | null;
  isAuthenticated: boolean;

  login: (access: string, refresh: string, user: import("../types").UserProfile) => void;
  logout: () => void;
  setUser: (user: import("../types").UserProfile) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: localStorage.getItem("access_token"),
  refreshToken: localStorage.getItem("refresh_token"),
  user: null,
  isAuthenticated: !!localStorage.getItem("access_token"),

  login: (access, refresh, user) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    set({ accessToken: access, refreshToken: refresh, user, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
  },
  setUser: (user) => set({ user }),
}));

// Period store
interface PeriodState {
  currentPeriod: import("../types").PayrollPeriod | null;
  setPeriod: (p: import("../types").PayrollPeriod) => void;
}

export const usePeriodStore = create<PeriodState>((set) => ({
  currentPeriod: null,
  setPeriod: (p) => set({ currentPeriod: p }),
}));

// Notification store
interface NotificationState {
  message: string;
  severity: "success" | "error" | "warning" | "info";
  open: boolean;
  show: (msg: string, sev?: "success" | "error" | "warning" | "info") => void;
  hide: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  message: "",
  severity: "info",
  open: false,
  show: (msg, sev = "info") => set({ message: msg, severity: sev, open: true }),
  hide: () => set({ open: false }),
}));
