/**
 * 英雄区域组件
 * Hero section - main landing area with headline, CTAs, and stats
 */
"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, User, Building2, Briefcase } from "lucide-react";

const ctas = [
  {
    text: "个人开发者",
    subtext: "按次付费",
    href: "/pricing",
    variant: "default" as const,
    icon: User,
  },
  {
    text: "企业团队",
    subtext: "批量优惠",
    href: "/pricing",
    variant: "outline" as const,
    icon: Building2,
  },
  {
    text: "代理机构",
    subtext: "合作方案",
    href: "/pricing#agency",
    variant: "ghost" as const,
    icon: Briefcase,
  },
];

const stats = [
  { value: "89%", label: "首审通过率", description: "远高于行业平均水平" },
  { value: "2000+", label: "累计下证", description: "涵盖软著、专利、商标" },
  { value: "30分钟", label: "平均生成", description: "从代码到完整材料" },
  { value: "¥19.0", label: "按次价格", description: "低门槛按单购买" },
];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-primary/10 via-background to-background">
      <div className="container py-24 md:py-32">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Content */}
          <div className="space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm">
              <span className="flex h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse" />
              AI 驱动的知识产权申请平台
            </div>

            {/* Headline */}
            <div className="space-y-4">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">
                一句话生成全套
                <span className="block text-primary">软著申请材料</span>
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl">
                30分钟完成符合版权中心要求的完整申请材料，89%首审通过率。
                告别繁琐手工，让AI为您处理一切。
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              {ctas.map((cta) => (
                <Button
                  key={cta.href}
                  asChild
                  variant={cta.variant}
                  size="lg"
                  className="flex-1 sm:flex-none h-auto py-6 px-8 text-base"
                >
                  <Link href={cta.href} className="flex items-center gap-2">
                    <cta.icon className="h-5 w-5" />
                    <div className="text-left">
                      <div>{cta.text}</div>
                      <div className="text-xs opacity-80">{cta.subtext}</div>
                    </div>
                  </Link>
                </Button>
              ))}
            </div>

            {/* Trust Badge */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <svg
                  className="h-5 w-5 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>无需信用卡</span>
              </div>
              <div className="flex items-center gap-2">
                <svg
                  className="h-5 w-5 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>支持按次付费</span>
              </div>
              <div className="flex items-center gap-2">
                <svg
                  className="h-5 w-5 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>5分钟快速上手</span>
              </div>
            </div>
          </div>

          {/* Right: Visual/Code Preview */}
          <div className="relative hidden lg:block">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-purple-500/20 rounded-3xl blur-3xl" />
            <div className="relative bg-card border rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                </div>
                <div className="flex-1 text-center text-sm text-muted-foreground">
                  IPFlow - 智能软著生成
                </div>
              </div>
              <div className="space-y-3 font-mono text-sm">
                <div className="flex gap-2">
                  <span className="text-blue-500">$</span>
                  <span>ipflow generate --type copyright</span>
                </div>
                <div className="text-muted-foreground">
                  ✅ 上传代码包 (42个文件)
                </div>
                <div className="text-muted-foreground">
                  ✅ 分析代码结构 (Python/TypeScript)
                </div>
                <div className="text-muted-foreground">
                  ✅ 生成操作说明书 (自动识别功能模块)
                </div>
                <div className="text-muted-foreground">
                  ✅ 排版源代码 (前30页 + 后30页)
                </div>
                <div className="text-green-500">
                  ⚡ 材料生成完成！耗时: 28分钟
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Banner */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="text-center space-y-2 p-6 rounded-xl bg-card/50 border backdrop-blur"
            >
              <div className="text-3xl md:text-4xl font-bold text-primary">
                {stat.value}
              </div>
              <div className="font-medium">{stat.label}</div>
              <div className="text-sm text-muted-foreground">
                {stat.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
