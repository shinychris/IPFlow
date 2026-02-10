import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { useAuth } from "@/hooks/use-auth";
import { Loader2 } from "lucide-react";
import NotFound from "@/pages/not-found";
import DashboardPage from "@/pages/dashboard";
import ProjectsPage from "@/pages/projects";
import TypeProjectsPage from "@/pages/type-projects";
import ProjectWizardPage from "@/pages/project-wizard";
import RulesPage from "@/pages/rules";
import HelpPage from "@/pages/help";
import SettingsPage from "@/pages/settings";
import LoginPage from "@/pages/login";
import RegisterPage from "@/pages/register";

function ProtectedRouter() {
  return (
    <Switch>
      <Route path="/" component={DashboardPage} />
      <Route path="/projects" component={ProjectsPage} />
      <Route path="/copyright">{() => <TypeProjectsPage type="copyright" />}</Route>
      <Route path="/patent">{() => <TypeProjectsPage type="patent" />}</Route>
      <Route path="/trademark">{() => <TypeProjectsPage type="trademark" />}</Route>
      <Route path="/project/new" component={ProjectWizardPage} />
      <Route path="/project/:id" component={ProjectWizardPage} />
      <Route path="/settings" component={SettingsPage} />
      <Route path="/rules" component={RulesPage} />
      <Route path="/help" component={HelpPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function AuthRouter() {
  return (
    <Switch>
      <Route path="/login" component={LoginPage} />
      <Route path="/register" component={RegisterPage} />
      <Route>{() => <LoginPage />}</Route>
    </Switch>
  );
}

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

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
  };

  return (
    <SidebarProvider style={sidebarStyle as React.CSSProperties}>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <header className="sticky top-0 z-50 flex items-center justify-between gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 py-2">
            <SidebarTrigger data-testid="button-sidebar-toggle" />
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

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="ip-kit-theme">
        <TooltipProvider>
          <AppContent />
          <Toaster />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
