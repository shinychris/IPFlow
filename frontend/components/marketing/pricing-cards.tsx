/**
 * 定价卡片组件
 * Pricing cards - display subscription plans
 */
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PricingPlan } from "@/types/marketing";

const pricingPlans: PricingPlan[] = [
  {
    id: "single",
    name: "按次付费",
    slug: "single",
    price: { monthly: 19, yearly: 19 },
    description: "单次申请，按单结算",
    badge: "灵活付费",
    badgeColor: "bg-emerald-500",
    features: [
      "按次付费：¥19.0/次",
      "支持软著申请主流程",
      "基础代码处理与导出",
      "支付后立即可用",
      "未通过可联系客服退款",
    ],
    limits: {
      maxProjects: 1,
      maxStorageGb: 0.5,
      maxMembers: 1,
    },
    ctaText: "立即按次购买",
    highlighted: true,
  },
  {
    id: "starter",
    name: "基础版",
    slug: "starter",
    price: { monthly: 49, yearly: 490 },
    description: "适合个人开发者",
    badge: "订阅版",
    badgeColor: "bg-blue-500",
    features: [
      "10个软著申请项目",
      "1GB存储空间",
      "高级代码处理",
      "AI辅助说明书生成",
      "导出完整申请材料",
      "邮件支持",
    ],
    limits: {
      maxProjects: 10,
      maxStorageGb: 1,
      maxMembers: 1,
    },
    ctaText: "立即购买",
    highlighted: false,
  },
  {
    id: "professional",
    name: "专业版",
    slug: "professional",
    price: { monthly: 199, yearly: 1990 },
    description: "适合小型团队",
    badge: "团队推荐",
    badgeColor: "bg-purple-500",
    features: [
      "10个软著/专利/商标项目",
      "10GB存储空间",
      "全部业务类型支持",
      "团队协作功能 (3人)",
      "优先技术支持",
      "批量导出功能",
      "AI智能优化",
    ],
    limits: {
      maxProjects: 10,
      maxStorageGb: 10,
      maxMembers: 3,
    },
    ctaText: "立即购买",
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "企业版",
    slug: "enterprise",
    price: { monthly: 999, yearly: 9990 },
    description: "适合中大型企业",
    badge: "企业",
    badgeColor: "bg-amber-500",
    features: [
      "100个项目数量",
      "100GB存储空间",
      "无限团队成员",
      "专属客户经理",
      "SLA服务保障",
      "定制化功能开发",
      "私有化部署选项",
    ],
    limits: {
      maxProjects: 100,
      maxStorageGb: 100,
      maxMembers: -1,
    },
    ctaText: "联系销售",
    highlighted: false,
  },
  {
    id: "agency",
    name: "代理机构版",
    slug: "agency",
    price: { monthly: 1999, yearly: 19990 },
    description: "适合知识产权代理机构",
    badge: "代理专用",
    badgeColor: "bg-emerald-500",
    features: [
      "500个项目/客户",
      "1TB存储空间",
      "20个团队成员",
      "客户管理功能",
      "白标定制服务",
      "API接口访问",
      "批量处理工具",
      "专属技术支持",
    ],
    limits: {
      maxProjects: 500,
      maxStorageGb: 1000,
      maxMembers: 20,
    },
    ctaText: "联系销售",
    highlighted: false,
  },
];

interface PricingCardsProps {
  billingInterval: "monthly" | "yearly";
  onPlanSelect: (planId: string) => void;
}

export function PricingCards({ billingInterval, onPlanSelect }: PricingCardsProps) {
  const getYearlySavings = (plan: PricingPlan) => {
    if (plan.price.monthly === 0) return null;
    const yearlyMonthly = plan.price.yearly / 12;
    const savings = Math.round((1 - yearlyMonthly / plan.price.monthly) * 100);
    return savings;
  };

  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
      {pricingPlans.map((plan) => {
        const savings = getYearlySavings(plan);
        const isSinglePlan = plan.id === "single";
        const price = billingInterval === "monthly" ? plan.price.monthly : plan.price.yearly;

        return (
          <Card
            key={plan.id}
            className={cn(
              "relative flex flex-col",
              plan.highlighted && "border-primary shadow-lg scale-105"
            )}
          >
            {plan.badge && (
              <Badge
                className={cn(
                  "absolute -top-3 left-1/2 -translate-x-1/2",
                  plan.badgeColor
                )}
              >
                {plan.badge}
              </Badge>
            )}

            <CardHeader>
              <CardTitle className="text-xl">{plan.name}</CardTitle>
              <CardDescription>{plan.description}</CardDescription>
            </CardHeader>

            <CardContent className="flex-1 space-y-6">
              {/* Price */}
              <div className="space-y-2">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold">
                    {isSinglePlan ? `¥${price.toFixed(1)}` : `¥${price}`}
                  </span>
                  {isSinglePlan ? (
                    <span className="text-muted-foreground">/次</span>
                  ) : (
                    <span className="text-muted-foreground">
                      /{billingInterval === "monthly" ? "月" : "年"}
                    </span>
                  )}
                </div>
                {billingInterval === "yearly" && savings && !isSinglePlan && (
                  <div className="text-sm text-green-600 dark:text-green-400">
                    年付节省 {savings}%
                  </div>
                )}
              </div>

              {/* Features */}
              <ul className="space-y-3">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>

            <CardFooter>
              <Button
                className={cn(
                  "w-full",
                  plan.highlighted && "bg-primary hover:bg-primary/90"
                )}
                variant={plan.highlighted ? "default" : "outline"}
                onClick={() => onPlanSelect(plan.id)}
              >
                {plan.ctaText}
                {price > 0 && <ArrowRight className="ml-2 h-4 w-4" />}
              </Button>
            </CardFooter>
          </Card>
        );
      })}
    </div>
  );
}
