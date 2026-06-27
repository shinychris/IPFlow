"use client";

import { useAuth } from "@/hooks/use-auth";
import { useAuthStore } from "@/stores/auth-store";
import { Loader2 } from "lucide-react";
import { redirect } from "next/navigation";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  // 等待 Zustand persist 从 localStorage 水合完成，避免刷新时
  // 已登录用户看到登录页闪现（与 dashboard 布局守卫保持一致）
  const hasHydrated = useAuthStore((s) => s.hasHydrated);

  if (isLoading || !hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isAuthenticated) {
    redirect("/dashboard");
  }

  return <>{children}</>;
}
