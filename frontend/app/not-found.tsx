"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-6xl font-bold text-primary">404</h1>
          <h2 className="text-2xl font-semibold">页面未找到</h2>
          <p className="text-muted-foreground">
            抱歉，您访问的页面不存在或已被移除
          </p>
        </div>
        <div className="flex gap-4 justify-center">
          <Link href="/">
            <Button>
              <Home className="mr-2 h-4 w-4" />
              返回首页
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
