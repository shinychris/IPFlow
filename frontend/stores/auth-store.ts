/**
 * 认证状态管理 (Zustand)
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authApi } from "@/api/auth";
import type { User, LoginRequest, RegisterRequest } from "@/types";

interface AuthState {
  // 状态
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  /** persist 是否已完成水合（用于路由守卫避免 hydration 竞态误重定向） */
  hasHydrated: boolean;
  /** 当前激活的组织 ID（租户上下文，注入 X-Tenant-ID）*/
  activeOrgId: string | null;

  // Actions
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  refreshAccessToken: () => Promise<string>;
  setActiveOrg: (orgId: string) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      hasHydrated: false,
      activeOrgId: null,

      // 登录
      login: async (data: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(data);
          if (response.success && response.data) {
            set({
              accessToken: response.data.access_token,
              refreshToken: response.data.refresh_token || null,
              isAuthenticated: true,
              isLoading: false,
            });
            // 获取用户信息
            await get().fetchUser();
          } else {
            set({
              error: response.message || "登录失败",
              isLoading: false,
            });
          }
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "登录失败",
            isLoading: false,
          });
        }
      },

      // 注册
      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.register(data);
          if (response.success) {
            // 注册成功后自动登录
            await get().login({
              username: data.username,
              password: data.password,
            });
          } else {
            set({
              error: response.message || "注册失败",
              isLoading: false,
            });
          }
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "注册失败",
            isLoading: false,
          });
        }
      },

      // 登出
      logout: async () => {
        try {
          await authApi.logout();
        } catch {
          // 忽略 logout API 错误（如 401）
        } finally {
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
            activeOrgId: null,
          });
        }
      },

      // 获取用户信息
      fetchUser: async () => {
        try {
          const response = await authApi.getMe();
          if (response.success && response.data) {
            set({ user: response.data });
            // 解析当前用户的默认组织（用于租户上下文 X-Tenant-ID）。
            // 个人组织在注册时由后端自动创建，取列表第一个作为默认。
            try {
              const { get } = await import("@/api/client");
              const orgs = await get<
                Array<{ id: string }>
              >("/organizations");
              if (orgs && orgs.length > 0 && !get().activeOrgId) {
                set({ activeOrgId: orgs[0].id });
              }
            } catch {
              // 组织列表获取失败不阻断登录流程
            }
          }
        } catch (error) {
          // 获取失败时登出
          get().logout();
        }
      },

      // 刷新访问令牌
      refreshAccessToken: async (): Promise<string> => {
        const currentRefreshToken = get().refreshToken;
        if (!currentRefreshToken) {
          throw new Error("No refresh token");
        }

        const response = await authApi.refreshToken(currentRefreshToken);
        if (response.success && response.data) {
          set({ accessToken: response.data.access_token });
          return response.data.access_token;
        }
        throw new Error("Failed to refresh token");
      },

      // 设置当前激活组织（租户上下文）
      setActiveOrg: (orgId: string) => set({ activeOrgId: orgId }),

      // 清除错误
      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        activeOrgId: state.activeOrgId,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.hasHydrated = true;
        }
      },
    }
  )
);
