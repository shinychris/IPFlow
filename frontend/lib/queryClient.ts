import { QueryClient, QueryFunction } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";

function normalizeApiPath(url: string): string {
  if (url.startsWith("/api/v1/")) {
    return url;
  }
  if (url.startsWith("/api/")) {
    return url.replace("/api/", "/api/v1/");
  }
  return url;
}

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

async function refreshAccessTokenIfPossible(): Promise<string | null> {
  const { refreshToken } = useAuthStore.getState();
  if (!refreshToken) return null;

  const refreshRes = await fetch("/api/v1/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!refreshRes.ok) {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
    return null;
  }

  const payload = await refreshRes.json();
  const nextToken = payload?.data?.access_token as string | undefined;
  if (!nextToken) return null;

  useAuthStore.setState({
    accessToken: nextToken,
    isAuthenticated: true,
  });
  return nextToken;
}

async function authenticatedFetch(url: string, init?: RequestInit): Promise<Response> {
  const { accessToken } = useAuthStore.getState();
  const headers = new Headers(init?.headers);
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  let res = await fetch(url, {
    ...init,
    headers,
    credentials: "include",
  });

  if (res.status !== 401) {
    return res;
  }

  const refreshedToken = await refreshAccessTokenIfPossible();
  if (!refreshedToken) {
    return res;
  }

  const retryHeaders = new Headers(init?.headers);
  retryHeaders.set("Authorization", `Bearer ${refreshedToken}`);
  res = await fetch(url, {
    ...init,
    headers: retryHeaders,
    credentials: "include",
  });

  return res;
}

export async function apiRequest(
  method: string,
  url: string,
  data?: unknown | undefined,
): Promise<Response> {
  const res = await authenticatedFetch(normalizeApiPath(url), {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
  });

  await throwIfResNotOk(res);
  return res;
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    const url = normalizeApiPath(queryKey.join("/") as string);
    const res = await authenticatedFetch(url);

    if (unauthorizedBehavior === "returnNull" && res.status === 401) {
      return null;
    }

    await throwIfResNotOk(res);
    return await res.json();
  };

// 这个函数用于在组件外部创建 QueryClient 实例
// 避免在 Next.js 的 SSR/CSR 边界出现问题
export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        queryFn: getQueryFn({ on401: "throw" }),
        refetchInterval: false,
        refetchOnWindowFocus: false,
        staleTime: Infinity,
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export const queryKeys = {
  copyrightGenerationContext: (projectId: string) =>
    [`/api/v1/copyright/projects/${projectId}/generation-context`] as const,
  copyrightGenerationJobs: (projectId: string) =>
    [`/api/v1/copyright/projects/${projectId}/generation-jobs`] as const,
  copyrightExportJobs: (projectId: string) =>
    [`/api/v1/copyright/projects/${projectId}/export-jobs`] as const,
};
