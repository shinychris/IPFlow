/**
 * UI 状态管理 (Zustand)
 */

import { create } from "zustand";

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: "default" | "destructive" | "success";
}

interface UIState {
  // 侧边栏状态
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // 主题状态
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;

  // Toast 状态
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;

  // 加载状态
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;

  // 确认对话框
  confirmDialog: {
    isOpen: boolean;
    title: string;
    description: string;
    onConfirm: (() => void) | null;
    onCancel: (() => void) | null;
  };
  openConfirmDialog: (options: {
    title: string;
    description: string;
    onConfirm: () => void;
    onCancel?: () => void;
  }) => void;
  closeConfirmDialog: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  // 侧边栏
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),

  // 主题
  theme: "light",
  setTheme: (theme) => set({ theme }),

  // Toast
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
    // 3秒后自动移除
    setTimeout(() => {
      get().removeToast(id);
    }, 3000);
  },
  removeToast: (id: string) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  // 全局加载
  globalLoading: false,
  setGlobalLoading: (loading) => set({ globalLoading: loading }),

  // 确认对话框
  confirmDialog: {
    isOpen: false,
    title: "",
    description: "",
    onConfirm: null,
    onCancel: null,
  },
  openConfirmDialog: (options) =>
    set({
      confirmDialog: {
        isOpen: true,
        title: options.title,
        description: options.description,
        onConfirm: options.onConfirm,
        onCancel: options.onCancel || null,
      },
    }),
  closeConfirmDialog: () =>
    set({
      confirmDialog: {
        isOpen: false,
        title: "",
        description: "",
        onConfirm: null,
        onCancel: null,
      },
    }),
}));
