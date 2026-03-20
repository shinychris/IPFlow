/**
 * 四步流程展示组件
 * Process steps - show the 4-step workflow
 */
import { Upload, FileEdit, Wand2, Download, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

const steps = [
  {
    step: 1,
    title: "上传代码",
    description: "支持40+编程语言，自动抽取前30页+后30页",
    icon: Upload,
    estimatedTime: "2分钟",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  {
    step: 2,
    title: "填写信息",
    description: "软件名称、版本号、开发语言等基本信息",
    icon: FileEdit,
    estimatedTime: "3分钟",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  {
    step: 3,
    title: "AI生成",
    description: "自动生成操作说明书，完成60页代码排版",
    icon: Wand2,
    estimatedTime: "20分钟",
    color: "text-pink-500",
    bgColor: "bg-pink-500/10",
  },
  {
    step: 4,
    title: "导出提交",
    description: "一键导出完整申请材料，直接提交版权中心",
    icon: Download,
    estimatedTime: "1分钟",
    color: "text-green-500",
    bgColor: "bg-green-500/10",
  },
];

export function ProcessSteps() {
  return (
    <section className="py-24 bg-muted/30">
      <div className="container">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            简单4步，轻松完成软著申请
          </h2>
          <p className="text-lg text-muted-foreground">
            无需专业知识，AI 自动处理所有复杂步骤。从代码到完整材料，最快30分钟搞定。
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, index) => (
            <div key={step.step} className="relative">
              <div className="bg-card border rounded-xl p-6 h-full">
                {/* Step Number */}
                <div className="flex items-start justify-between mb-4">
                  <div
                    className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-xl",
                      step.bgColor
                    )}
                  >
                    <step.icon className={cn("h-6 w-6", step.color)} />
                  </div>
                  <span className="text-4xl font-bold text-muted-foreground/20">
                    0{step.step}
                  </span>
                </div>

                {/* Content */}
                <div className="space-y-3">
                  <h3 className="text-xl font-semibold">{step.title}</h3>
                  <p className="text-muted-foreground text-sm">
                    {step.description}
                  </p>
                  <div className="flex items-center gap-2 text-sm font-medium text-primary">
                    <span>{step.estimatedTime}</span>
                  </div>
                </div>
              </div>

              {/* Arrow Connector (Desktop) */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-3 transform -translate-y-1/2 z-10">
                  <ArrowRight className="h-6 w-6 text-muted-foreground/30" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-muted-foreground mb-4">
            总耗时约 26 分钟，比传统方式节省 90% 时间
          </p>
        </div>
      </div>
    </section>
  );
}
