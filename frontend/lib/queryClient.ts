import { QueryClient, QueryFunction } from "@tanstack/react-query";

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

export async function apiRequest(
  method: string,
  url: string,
  data?: unknown | undefined,
): Promise<Response> {
  const res = await fetch(normalizeApiPath(url), {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
    credentials: "include",
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
    const res = await fetch(url, {
      credentials: "include",
    });

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
