/**
 * CTA 区域组件
 * Call-to-action section - bottom conversion area
 */
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, CheckCircle2 } from "lucide-react";

const benefits = [
  "新增按次付费，¥19.0/次",
  "支持软著、专利、商标三大业务",
  "未通过可联系客服退款",
  "89%首审通过率，远超行业平均",
  "30分钟生成材料，节省90%时间"
];

export function CTASection() {
  return (
    <section className="py-24 bg-primary text-primary-foreground">
      <div className="container">
        <div className="max-w-3xl mx-auto text-center space-y-8">
          {/* Headline */}
          <div className="space-y-4">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold">
              准备好开始了吗？
            </h2>
            <p className="text-xl text-primary-foreground/80">
              加入 5000+ 开发者团队，用 AI 驱动的方式完成知识产权申请。
            </p>
          </div>

          {/* Benefits List */}
          <div className="grid sm:grid-cols-2 gap-4 text-left max-w-2xl mx-auto">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-green-300" />
                <span>{benefit}</span>
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              asChild
              size="lg"
              variant="secondary"
              className="h-auto py-6 px-8 text-lg"
            >
              <Link href="/register" className="flex items-center gap-2">
                立即开始使用
                <ArrowRight className="h-5 w-5" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-auto py-6 px-8 text-lg border-primary-foreground/20 hover:bg-primary-foreground/10"
            >
              <Link href="/pricing">查看定价方案</Link>
            </Button>
          </div>

          {/* Trust Note */}
          <p className="text-sm text-primary-foreground/60">
            无需信用卡 · 随时可以取消 · 7天24小时支持
          </p>
        </div>
      </div>
    </section>
  );
}
