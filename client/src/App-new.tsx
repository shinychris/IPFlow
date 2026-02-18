/**
 * 应用入口 (重构版)
 * 
 * 使用 Zustand 替代 React Query
 */

import { Switch, Route } from "wouter";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { useAuthStore } from "@/stores/auth-store";
import { Loader2 } from "lucide-react";

// 页面导入
import NotFound from "@/pages/not-found";
import DashboardPage from "@/pages/dashboard-new";
import ProjectsPage from "@/pages/projects-new";
import LoginPage from "@/pages/login-new";
import RegisterPage from "@/pages/register";

// 保护路由组件
function ProtectedRouter() {
  return (
    <Switch>
      <Route path="/" component={DashboardPage} />
      <Route path="/projects" component={ProjectsPage} />
      {/* 保留旧页面作为兼容 */}
      <Route path="/copyright" component={() => <div>软著项目（旧版）</div>} />
      <Route path="/patent" component={() => <div>专利项目（旧版）</div>} />
      <Route path="/trademark" component={() => <div>商标项目（旧版）</div>} />
      <Route path="/project/new" component={() => <div>新建项目（开发中）</div>} />
      <Route path="/project/:id" component={() => <div>项目详情（开发中）</div>} />
      <Route component={NotFound} />
    </Switch>
  );
}

// 认证路由组件
function AuthRouter() {
  return (
    <Switch>
      <Route path="/login" component={LoginPage} />
      <Route path="/register" component={RegisterPage} />
      <Route>{() => <LoginPage />}</Route>
    </Switch>
  );
}

// 应用内容
function AppContent() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthRouter />;
  }

  const sidebarStyle = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "3.5rem",
  } as React.CSSProperties;

  return (
    <SidebarProvider style={sidebarStyle}>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <header className="sticky top-0 z-50 flex items-center justify-between gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 py-2">
            <SidebarTrigger />
            <ThemeToggle />
          </header>
          <main className="flex-1 pb-20">
            <ProtectedRouter />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}

// 主应用
function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="ip-kit-theme">
      <TooltipProvider>
        <AppContent />
        <Toaster />
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default App;
