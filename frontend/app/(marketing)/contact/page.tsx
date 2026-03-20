"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ContactPage() {
  return (
    <main className="container py-20">
      <div className="mx-auto max-w-2xl space-y-6 text-center">
        <h1 className="text-3xl font-bold">联系销售</h1>
        <p className="text-muted-foreground">
          企业版与代理版请联系销售团队获取专属报价、部署支持与 SLA 方案。
        </p>
        <div className="rounded-lg border p-6 text-left">
          <p>邮箱：sales@ipflow.com</p>
          <p>电话：400-800-2026</p>
          <p>工作时间：工作日 09:00 - 18:00</p>
        </div>
        <div className="flex justify-center gap-3">
          <Link href="/pricing">
            <Button variant="outline">返回定价页</Button>
          </Link>
          <Link href="/register">
            <Button>先免费注册</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
