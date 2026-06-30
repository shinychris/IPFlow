"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
import { Loader2, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  subscriptionsApi,
  type Plan,
  type Subscription,
  type Invoice,
  type UsageStats,
} from "@/api/subscriptions";
import { createPayment } from "@/api/payments";

const planInterval = (sub?: Subscription | null) =>
  (sub?.interval as "monthly" | "yearly" | undefined) ?? "monthly";

const priceLabel = (plan: Plan, interval: "monthly" | "yearly") => {
  const monthly = plan.price_monthly ?? 0;
  const yearly = plan.price_yearly ?? 0;
  if (interval === "yearly" && yearly) {
    return `¥${yearly} / 年`;
  }
  return `¥${monthly} / 月`;
};

const limitsLabel = (plan: Plan): string => {
  const limits = plan.limits || {};
  const parts: string[] = [];
  if (limits.max_projects != null) {
    parts.push(
      `${limits.max_projects === -1 ? "无限" : limits.max_projects} 项目`,
    );
  }
  if (limits.max_storage_bytes != null) {
    const mb = limits.max_storage_bytes / (1024 * 1024);
    parts.push(mb >= 1024 ? `${(mb / 1024).toFixed(0)}GB 存储` : `${mb.toFixed(0)}MB 存储`);
  }
  if (limits.max_members != null) {
    parts.push(
      `${limits.max_members === -1 ? "无限" : limits.max_members} 成员`,
    );
  }
  return parts.join(" · ") || "—";
};

function UsageProgress({
  label,
  used,
  limit,
  unit = "",
}: {
  label: string;
  used: number;
  limit: number | null | undefined;
  unit?: string;
}) {
  const limitNum = limit ?? 0;
  const unlimited = limit === -1 || limit == null;
  const pct = unlimited ? 0 : limitNum > 0 ? Math.min(100, (used / limitNum) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">
          {used}
          {unit}
          {unlimited ? " / 无限" : limitNum > 0 ? ` / ${limitNum}${unit}` : ""}
        </span>
      </div>
      {!unlimited && limitNum > 0 ? (
        <div className="h-2 w-full overflow-hidden rounded bg-muted">
          <div
            className="h-full rounded bg-primary"
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
    </div>
  );
}

export default function SubscriptionsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Stripe Checkout 支付成功 / 取消回跳提示
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("paid") === "1") {
      toast({ title: "支付成功", description: "订阅已激活，刷新可见最新计划" });
      queryClient.invalidateQueries({ queryKey: ["/subscriptions/current"] });
      queryClient.invalidateQueries({ queryKey: ["/subscriptions/usage"] });
      window.history.replaceState({}, "", window.location.pathname);
    } else if (params.get("canceled") === "1") {
      toast({
        title: "支付已取消",
        description: "您尚未被扣款，可随时重新订阅",
        variant: "destructive",
      });
      window.history.replaceState({}, "", window.location.pathname);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { data: plans = [], isLoading: plansLoading } = useQuery({
    queryKey: ["/subscriptions/plans"],
    queryFn: () => subscriptionsApi.listPlans(),
    retry: false,
  });

  const { data: current, isLoading: subLoading } = useQuery({
    queryKey: ["/subscriptions/current"],
    queryFn: () => subscriptionsApi.getCurrent(),
    retry: false,
  });

  const { data: usage } = useQuery({
    queryKey: ["/subscriptions/usage"],
    queryFn: () => subscriptionsApi.getUsage(),
    retry: false,
  });

  const { data: invoices = [] } = useQuery({
    queryKey: ["/subscriptions/invoices"],
    queryFn: () => subscriptionsApi.listInvoices(),
    retry: false,
  });

  const subscribeMutation = useMutation({
    mutationFn: async (planId: string) => {
      // 商业化路径：通过 Stripe Checkout 完成真实收款。
      // 创建支付订单 → 跳转到 Stripe 托管支付页 → 支付成功后 Webhook 激活订阅。
      const interval = planInterval(current);
      const order = await createPayment({
        planId,
        billingInterval: interval,
        paymentMethod: "stripe",
      });
      // 后端把 Stripe Checkout URL 写入 payUrl 字段
      if (order.payUrl) {
        window.location.href = order.payUrl;
      } else {
        throw new Error("未返回 Stripe 支付链接，请检查后端 STRIPE_* 配置");
      }
      return order;
    },
    onSuccess: () => {
      // 页面即将跳转到 Stripe，无需 toast；支付成功回跳后由 ?paid=1 提示
      queryClient.invalidateQueries({ queryKey: ["/subscriptions/current"] });
      queryClient.invalidateQueries({ queryKey: ["/subscriptions/usage"] });
    },
    onError: (error: any) => {
      toast({
        title: "发起支付失败",
        description:
          error?.response?.data?.detail || error?.message || "请稍后重试",
        variant: "destructive",
      });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => subscriptionsApi.cancel(true),
    onSuccess: () => {
      toast({ title: "已取消", description: "订阅将在当前周期结束后失效" });
      queryClient.invalidateQueries({ queryKey: ["/subscriptions/current"] });
    },
    onError: (error: any) => {
      toast({
        title: "取消失败",
        description: error?.response?.data?.detail || "请稍后重试",
        variant: "destructive",
      });
    },
  });

  const currentPlanId = current?.plan_id ?? current?.plan?.id;

  if (plansLoading || subLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="订阅与计费"
        description="管理您的订阅计划、用量与账单"
      />

      {/* 当前订阅与用量 */}
      <Card>
        <CardHeader>
          <CardTitle>当前订阅</CardTitle>
          <CardDescription>
            {current
              ? `当前计划：${current.plan?.name ?? current.plan_id ?? "—"}（${current.status ?? "—"}）`
              : "您当前没有有效订阅，默认为免费计划"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {current ? (
            <div className="flex items-center gap-3">
              <Badge variant="secondary">{current.status ?? "active"}</Badge>
              {current.cancel_at_period_end ? (
                <Badge variant="destructive">待取消</Badge>
              ) : null}
              {current.current_period_end ? (
                <span className="text-sm text-muted-foreground">
                  到期：{new Date(current.current_period_end).toLocaleDateString()}
                </span>
              ) : null}
              <Button
                variant="outline"
                size="sm"
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
              >
                {cancelMutation.isPending ? "处理中..." : "取消订阅"}
              </Button>
            </div>
          ) : null}

          {usage ? (
            <div className="grid gap-4 md:grid-cols-3">
              <UsageProgress
                label="项目数"
                used={(usage.projects as { used: number })?.used ?? 0}
                limit={(usage.projects as { limit: number | null })?.limit}
              />
              <UsageProgress
                label="存储"
                // 后端 StorageUsageStats 返回 used_gb / limit_gb（无单位后缀，由组件自处理）
                used={Number(
                  (usage.storage as { used_gb?: number; used_bytes?: number })
                    ?.used_gb ??
                    (usage.storage as { used_bytes?: number })?.used_bytes ??
                    0,
                )}
                limit={
                  (usage.storage as {
                    limit_gb?: number | null;
                    limit_bytes?: number | null;
                  })?.limit_gb ??
                  (usage.storage as { limit_bytes?: number | null })
                    ?.limit_bytes ??
                  null
                }
              />
              <UsageProgress
                label="成员数"
                used={(usage.members as { used: number })?.used ?? 0}
                limit={(usage.members as { limit: number | null })?.limit}
              />
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* 可选计划 */}
      <div>
        <h3 className="mb-3 text-lg font-semibold">选择计划</h3>
        <div className="grid gap-4 md:grid-cols-3">
          {plans.map((plan) => {
            const isCurrent = plan.id === currentPlanId;
            return (
              <Card
                key={plan.id}
                className={isCurrent ? "border-primary" : ""}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{plan.name}</CardTitle>
                    {isCurrent ? (
                      <Badge>当前</Badge>
                    ) : null}
                  </div>
                  <CardDescription>{plan.description || limitsLabel(plan)}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-2xl font-bold">
                    {priceLabel(plan, planInterval(current))}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {limitsLabel(plan)}
                  </div>
                  <Button
                    className="w-full"
                    variant={isCurrent ? "outline" : "default"}
                    disabled={isCurrent || subscribeMutation.isPending}
                    onClick={() => subscribeMutation.mutate(plan.id)}
                  >
                    {isCurrent ? (
                      <>
                        <Check className="mr-2 h-4 w-4" /> 当前计划
                      </>
                    ) : subscribeMutation.isPending ? (
                      "处理中..."
                    ) : (
                      "切换到该计划"
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
          {plans.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              暂无可选计划（后端未配置或未启用订阅模块）。
            </p>
          ) : null}
        </div>
      </div>

      {/* 账单记录 */}
      <Card>
        <CardHeader>
          <CardTitle>账单记录</CardTitle>
        </CardHeader>
        <CardContent>
          {(invoices as Invoice[]).length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无账单记录</p>
          ) : (
            <div className="space-y-2">
              {(invoices as Invoice[]).map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between rounded border p-3 text-sm"
                >
                  <div>
                    <div className="font-medium">
                      ¥{(inv as { amount_due?: number; amount_paid?: number }).amount_due ??
                        (inv as { amount_paid?: number }).amount_paid ??
                        "—"}
                      {inv.currency ? ` ${inv.currency}` : ""}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {inv.created_at
                        ? new Date(inv.created_at).toLocaleString()
                        : "—"}
                    </div>
                  </div>
                  <Badge variant="secondary">{inv.status ?? "—"}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
