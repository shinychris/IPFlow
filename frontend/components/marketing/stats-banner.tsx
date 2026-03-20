/**
 * 数据统计横幅组件
 * Stats banner - display key metrics
 */
import { TrendingUp, Users, FileText, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

const statItems = [
  {
    value: "89%",
    label: "首审通过率",
    icon: TrendingUp,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    trend: "+12%",
    trendLabel: "高于行业平均",
  },
  {
    value: "2000+",
    label: "累计下证数量",
    icon: FileText,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    trend: "+500",
    trendLabel: "本月新增",
  },
  {
    value: "5000+",
    label: "注册用户",
    icon: Users,
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
    trend: "+800",
    trendLabel: "本月新增",
  },
  {
    value: "30分钟",
    label: "平均生成时间",
    icon: Clock,
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    trend: "-70%",
    trendLabel: "比传统方式",
  },
];

export function StatsBanner() {
  return (
    <section className="py-16 border-y bg-muted/20">
      <div className="container">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {statItems.map((item, index) => (
            <div
              key={index}
              className="bg-card border rounded-xl p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={cn("p-3 rounded-lg", item.bgColor)}>
                  <item.icon className={cn("h-6 w-6", item.color)} />
                </div>
                {item.trend && (
                  <div className="flex items-center gap-1 text-sm font-medium text-green-600 dark:text-green-400">
                    <span>{item.trend}</span>
                  </div>
                )}
              </div>
              <div className="space-y-1">
                <div className="text-3xl font-bold">{item.value}</div>
                <div className="text-sm text-muted-foreground">
                  {item.label}
                </div>
                {item.trendLabel && (
                  <div className="text-xs text-muted-foreground mt-2">
                    {item.trendLabel}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
