/**
 * 功能卡片组件
 * Feature cards - showcase key features
 */
import { Code, FileText, Shield, Zap, Users, Globe } from "lucide-react";
import { cn } from "@/lib/utils";

const features = [
  {
    icon: Code,
    title: "智能代码处理",
    description: "支持40+编程语言，自动抽取代码关键部分，智能识别功能模块和算法逻辑。",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  {
    icon: FileText,
    title: "自动文档生成",
    description: "AI自动生成操作说明书，符合版权中心格式要求，无需手动编写。",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  {
    icon: Shield,
    title: "合规检查保障",
    description: "内置中国版权中心最新规范，自动检查材料完整性，确保一次通过。",
    color: "text-green-500",
    bgColor: "bg-green-500/10",
  },
  {
    icon: Zap,
    title: "极速生成体验",
    description: "30分钟完成全部材料，比传统方式节省90%时间，效率提升显著。",
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
  },
  {
    icon: Users,
    title: "团队协作功能",
    description: "支持多人协同编辑，权限精细控制，适合企业和团队使用。",
    color: "text-pink-500",
    bgColor: "bg-pink-500/10",
  },
  {
    icon: Globe,
    title: "三大业务支持",
    description: "软著、专利、商标一站式管理，满足企业全方位知识产权需求。",
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
  },
];

export function FeatureCards() {
  return (
    <section className="py-24">
      <div className="container">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            为什么选择 IPFlow？
          </h2>
          <p className="text-lg text-muted-foreground">
            我们致力于让知识产权申请变得简单、高效、可靠。每一项功能都为您的成功而设计。
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-card border rounded-xl p-6 hover:shadow-lg transition-all hover:-translate-y-1"
            >
              <div className={cn("p-3 rounded-lg w-fit mb-4", feature.bgColor)}>
                <feature.icon className={cn("h-6 w-6", feature.color)} />
              </div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
