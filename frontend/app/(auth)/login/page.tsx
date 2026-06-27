"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Loader2 } from "lucide-react";

export default function LoginPage() {
  const { login, error: authError } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  // 同步 auth store 的错误
  useEffect(() => {
    if (authError) {
      setError(typeof authError === 'string' ? authError : authError.message || '登录失败');
    }
  }, [authError]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login.mutateAsync({ username, password });
      // 登录成功，跳转到工作台
      // 使用硬跳转：确保 dashboard 布局的认证守卫能从已持久化的 localStorage
      // 读取 isAuthenticated（避免 Zustand persist 水合竞态导致被重定向回登录页）
      window.location.href = "/dashboard";
    } catch (err: any) {
      let errorMsg = "登录失败，请检查用户名和密码";
      if (err?.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
    }
  }

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 relative">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/80 to-primary/40" />
        <div className="relative z-10 flex flex-col items-center justify-center p-10 text-white text-center w-full">
          <h2 className="text-3xl font-bold mb-3">知识产权助手</h2>
          <p className="text-lg opacity-90 max-w-md">
            一站式知识产权申请材料制备平台，支持软著、专利、商标三大业务，助您高效完成申请。
          </p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center bg-background p-6 sm:p-10">
        <div className="w-full max-w-sm space-y-8">
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-bold" data-testid="text-login-title">登录</h1>
              <p className="text-sm text-muted-foreground mt-1">请输入账号信息登录系统</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm" data-testid="text-login-error">
                {typeof error === 'string' ? error : (error as Error)?.message || '登录失败'}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入用户名"
                autoComplete="username"
                data-testid="input-username"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
                autoComplete="current-password"
                data-testid="input-password"
              />
            </div>
            <Button
              type="submit"
              className="w-full"
              disabled={login.isPending}
              data-testid="button-login"
            >
              {login.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              登录
            </Button>
          </form>

          <div className="text-center text-sm text-muted-foreground">
            还没有账号？
            <Link href="/register" className="text-primary ml-1 hover:underline" data-testid="link-register">
              立即注册
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
