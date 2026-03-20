"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { HoverCard, HoverCardTrigger, HoverCardContent } from "@/components/ui/hover-card";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  FolderOpen,
  FileCode,
  Lightbulb,
  Stamp,
  HelpCircle,
  Shield,
  Settings,
  LogOut,
} from "lucide-react";

const mainNavItems = [
  {
    title: "工作台",
    url: "/dashboard",
    icon: LayoutDashboard,
  },
];

const businessItems = [
  {
    title: "软著申请",
    url: "/copyright",
    icon: FileCode,
  },
  {
    title: "专利申请",
    url: "/patent",
    icon: Lightbulb,
  },
  {
    title: "商标申请",
    url: "/trademark",
    icon: Stamp,
  },
];

const resourceItems = [
  {
    title: "所有项目",
    url: "/projects",
    icon: FolderOpen,
  },
  {
    title: "申请规范",
    url: "/rules",
    icon: Shield,
  },
  {
    title: "帮助文档",
    url: "/help",
    icon: HelpCircle,
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const initials = (user?.displayName || user?.username || "U").slice(0, 2).toUpperCase();

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-semibold">知识产权助手</span>
            <span className="text-xs text-muted-foreground">IP Application Kit</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNavItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={pathname === item.url}>
                    <Link href={item.url} data-testid={`nav-${item.url.replace("/", "") || "dashboard"}`}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>知识产权业务</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {businessItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={pathname.startsWith(item.url)}>
                    <Link href={item.url} data-testid={`nav-${item.url.replace("/", "")}`}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>资源中心</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {resourceItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={pathname === item.url}>
                    <Link href={item.url} data-testid={`nav-${item.url.replace("/", "")}`}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3">
        <div className="flex items-center gap-3 px-2 py-1.5">
          <HoverCard openDelay={200} closeDelay={300}>
            <HoverCardTrigger asChild>
              <button className="flex-shrink-0 cursor-pointer" data-testid="trigger-user-menu">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
              </button>
            </HoverCardTrigger>
            <HoverCardContent side="top" align="start" className="w-48 p-2">
              <div className="px-2 py-1.5 mb-1">
                <div className="text-sm font-medium truncate">{user?.displayName || user?.username}</div>
                <div className="text-xs text-muted-foreground truncate">{user?.role === "admin" ? "管理员" : "普通用户"}</div>
              </div>
              <Separator className="my-1" />
              <Link href="/settings">
                <div className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover-elevate cursor-pointer" data-testid="nav-settings">
                  <Settings className="h-4 w-4" />
                  <span>设置</span>
                </div>
              </Link>
              <div
                className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover-elevate cursor-pointer"
                onClick={() => logout.mutate()}
                data-testid="button-logout"
              >
                <LogOut className="h-4 w-4" />
                <span>退出登录</span>
              </div>
            </HoverCardContent>
          </HoverCard>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium truncate" data-testid="text-current-user">
              {user?.displayName || user?.username}
            </div>
            <div className="text-xs text-muted-foreground truncate">
              {user?.role === "admin" ? "管理员" : "普通用户"}
            </div>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
