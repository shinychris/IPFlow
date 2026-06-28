import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { authApi } from "@/api/auth";
import type { User } from "@shared/types";

type AuthUser = User;

export function useAuth() {
  const queryClient = useQueryClient();
  const store = useAuthStore();

  const {
    data: user,
    isLoading,
    error,
  } = useQuery<AuthUser | null>({
    queryKey: ["/api/auth/me"],
    queryFn: async () => {
      const response = await authApi.getMe();
      if (response.success && response.data) {
        return response.data as unknown as AuthUser;
      }
      return null;
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
    enabled: store.isAuthenticated, // 只有已认证时才获取用户信息
  });

  const loginMutation = useMutation({
    mutationFn: async (data: { username: string; password: string }) => {
      await store.login(data);
      // 注意：store 是渲染快照，await 后其 error 仍是旧值；
      // 必须用 getState() 读取最新状态，否则登录失败时错误不会抛出。
      const latestError = useAuthStore.getState().error;
      if (latestError) {
        throw new Error(latestError);
      }
    },
    onSuccess: async () => {
      // 登录成功后立即获取用户信息
      await store.fetchUser();
      queryClient.invalidateQueries({ queryKey: ["/api/auth/me"] });
    },
  });

  const registerMutation = useMutation({
    mutationFn: async (data: {
      username: string;
      email: string;
      password: string;
      displayName?: string;
    }) => {
      await store.register(data as any);
      // 同 login：用 getState() 读取注册后的最新错误
      const latestError = useAuthStore.getState().error;
      if (latestError) {
        throw new Error(latestError);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/auth/me"] });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await store.logout();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/auth/me"] });
    },
  });

  return {
    user: user ?? store.user ?? null,
    isLoading: store.isLoading || isLoading,
    isAuthenticated: store.isAuthenticated,
    login: loginMutation,
    register: registerMutation,
    logout: logoutMutation,
    error: store.error || error,
  };
}
