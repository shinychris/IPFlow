"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Loader2, ShieldAlert, Trash2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/use-auth";
import { adminApi } from "@/api/admin";

const isAdmin = (role: unknown) => role === "super_admin";

export default function AdminPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { user, isLoading: authLoading } = useAuth();
  const [userSearch, setUserSearch] = useState("");

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["/admin/dashboard"],
    queryFn: () => adminApi.getDashboard(),
    enabled: !!user && isAdmin(user.role),
    retry: false,
  });

  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ["/admin/users", userSearch],
    queryFn: () => adminApi.listUsers({ search: userSearch || undefined }),
    enabled: !!user && isAdmin(user.role),
    retry: false,
  });

  const { data: orgs = [], isLoading: orgsLoading } = useQuery({
    queryKey: ["/admin/organizations"],
    queryFn: () => adminApi.listOrganizations(),
    enabled: !!user && isAdmin(user.role),
    retry: false,
  });

  const { data: plans = [], isLoading: plansLoading } = useQuery({
    queryKey: ["/admin/plans"],
    queryFn: () => adminApi.listPlans(),
    enabled: !!user && isAdmin(user.role),
    retry: false,
  });

  const { data: auditLogs = [], isLoading: logsLoading } = useQuery({
    queryKey: ["/admin/audit-logs"],
    queryFn: () => adminApi.listAuditLogs({ per_page: 50 }),
    enabled: !!user && isAdmin(user.role),
    retry: false,
  });

  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deleteUser(userId),
    onSuccess: () => {
      toast({ title: "已删除", description: "用户已删除" });
      queryClient.invalidateQueries({ queryKey: ["/admin/users"] });
      queryClient.invalidateQueries({ queryKey: ["/admin/dashboard"] });
    },
    onError: (error: any) => {
      toast({
        title: "删除失败",
        description: error?.response?.data?.detail || "请重试",
        variant: "destructive",
      });
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: string;
      data: { role?: string; status?: string };
    }) => adminApi.updateUser(userId, data),
    onSuccess: () => {
      toast({ title: "已更新", description: "用户信息已更新" });
      queryClient.invalidateQueries({ queryKey: ["/admin/users"] });
    },
    onError: (error: any) => {
      toast({
        title: "更新失败",
        description: error?.response?.data?.detail || "请重试",
        variant: "destructive",
      });
    },
  });

  if (authLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!user || !isAdmin(user.role)) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <ShieldAlert className="h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">无访问权限</h2>
            <p className="text-muted-foreground mb-4">
              管理后台仅对管理员开放。
            </p>
            <Link href="/dashboard">
              <Button variant="outline">返回工作台</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="管理后台"
        description="系统仪表盘、用户、组织、计划与审计日志"
      />

      {/* 统计概览 */}
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
        <StatCard
          label="用户总数"
          value={stats?.total_users}
          loading={statsLoading}
        />
        <StatCard
          label="本月新增用户"
          value={stats?.new_users_this_month}
          loading={statsLoading}
        />
        <StatCard
          label="组织总数"
          value={stats?.total_organizations}
          loading={statsLoading}
        />
        <StatCard
          label="有效订阅"
          value={stats?.active_subscriptions}
          loading={statsLoading}
        />
        <StatCard
          label="项目总数"
          value={stats?.total_projects}
          loading={statsLoading}
        />
        <StatCard
          label="本月收入"
          value={stats?.revenue_this_month}
          prefix="¥"
          loading={statsLoading}
        />
      </div>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">用户</TabsTrigger>
          <TabsTrigger value="organizations">组织</TabsTrigger>
          <TabsTrigger value="plans">计划</TabsTrigger>
          <TabsTrigger value="audit">审计日志</TabsTrigger>
        </TabsList>

        {/* 用户管理 */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>用户管理</CardTitle>
              <CardDescription>
                <input
                  className="h-8 rounded-md border border-input bg-background px-3 text-sm"
                  placeholder="搜索用户名/邮箱..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                />
              </CardDescription>
            </CardHeader>
            <CardContent>
              {usersLoading ? (
                <LoadingRow />
              ) : users.length === 0 ? (
                <EmptyRow text="暂无用户" />
              ) : (
                <div className="space-y-2">
                  {users.map((u) => (
                    <div
                      key={u.id}
                      className="flex items-center justify-between rounded border p-3"
                    >
                      <div className="min-w-0">
                        <div className="font-medium truncate">
                          {u.display_name || u.username}
                          <span className="ml-2 text-xs text-muted-foreground">
                            {u.email}
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          注册：{new Date(u.created_at).toLocaleDateString()}
                          {u.last_login_at
                            ? ` · 最近登录：${new Date(u.last_login_at).toLocaleDateString()}`
                            : ""}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <select
                          className="h-8 rounded-md border border-input bg-background px-2 text-xs"
                          value={u.role}
                          onChange={(e) =>
                            updateUserMutation.mutate({
                              userId: u.id,
                              data: { role: e.target.value },
                            })
                          }
                        >
                          <option value="member">成员</option>
                          <option value="manager">经理</option>
                          <option value="admin">管理员</option>
                          <option value="super_admin">超级管理员</option>
                        </select>
                        <select
                          className="h-8 rounded-md border border-input bg-background px-2 text-xs"
                          value={u.status}
                          onChange={(e) =>
                            updateUserMutation.mutate({
                              userId: u.id,
                              data: { status: e.target.value },
                            })
                          }
                        >
                          <option value="active">激活</option>
                          <option value="inactive">未激活</option>
                          <option value="suspended">已封禁</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (
                              confirm(`确定删除用户「${u.username}」？此操作不可恢复。`)
                            ) {
                              deleteUserMutation.mutate(u.id);
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 组织管理 */}
        <TabsContent value="organizations">
          <Card>
            <CardHeader>
              <CardTitle>组织管理</CardTitle>
            </CardHeader>
            <CardContent>
              {orgsLoading ? (
                <LoadingRow />
              ) : orgs.length === 0 ? (
                <EmptyRow text="暂无组织" />
              ) : (
                <div className="space-y-2">
                  {orgs.map((o) => (
                    <div
                      key={o.id}
                      className="flex items-center justify-between rounded border p-3"
                    >
                      <div className="min-w-0">
                        <div className="font-medium truncate">
                          {o.name}
                          <span className="ml-2 text-xs text-muted-foreground">
                            {o.slug}
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          计划：{o.plan_type} · 成员：{o.member_count ?? "—"} ·
                          创建：{new Date(o.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {o.is_active ? (
                          <Badge variant="secondary">活跃</Badge>
                        ) : (
                          <Badge variant="destructive">停用</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 计划管理 */}
        <TabsContent value="plans">
          <Card>
            <CardHeader>
              <CardTitle>订阅计划</CardTitle>
            </CardHeader>
            <CardContent>
              {plansLoading ? (
                <LoadingRow />
              ) : plans.length === 0 ? (
                <EmptyRow text="暂无计划" />
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {plans.map((p) => (
                    <div key={p.id} className="rounded border p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{p.name}</span>
                        {p.is_active ? (
                          <Badge variant="secondary">启用</Badge>
                        ) : (
                          <Badge variant="outline">停用</Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        ¥{p.price_monthly}/月 · ¥{p.price_yearly}/年 ·{" "}
                        {p.currency}
                      </div>
                      {p.description ? (
                        <div className="text-xs text-muted-foreground mt-1">
                          {p.description}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 审计日志 */}
        <TabsContent value="audit">
          <Card>
            <CardHeader>
              <CardTitle>审计日志</CardTitle>
              <CardDescription>最近 50 条操作记录</CardDescription>
            </CardHeader>
            <CardContent>
              {logsLoading ? (
                <LoadingRow />
              ) : auditLogs.length === 0 ? (
                <EmptyRow text="暂无审计日志" />
              ) : (
                <div className="space-y-1 max-h-[480px] overflow-auto">
                  {auditLogs.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start gap-2 rounded border p-2 text-sm"
                    >
                      <Badge variant="outline" className="shrink-0">
                        {log.action}
                      </Badge>
                      <div className="min-w-0 flex-1">
                        <div className="truncate">
                          {log.description ||
                            `${log.resource_type}${
                              log.resource_id ? `:${log.resource_id}` : ""
                            }`}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleString()}
                          {log.ip_address ? ` · ${log.ip_address}` : ""}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({
  label,
  value,
  prefix = "",
  loading,
}: {
  label: string;
  value?: number | null;
  prefix?: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-2xl font-bold mt-1">
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          ) : (
            `${prefix}${value ?? 0}`
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function LoadingRow() {
  return (
    <div className="flex items-center justify-center py-8">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

function EmptyRow({ text }: { text: string }) {
  return (
    <p className="text-sm text-muted-foreground text-center py-8">{text}</p>
  );
}
