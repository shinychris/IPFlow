/**
 * 功能对比表组件
 * Plan comparison table - compare features across plans
 */
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

const comparisonFeatures = [
  {
    category: "项目数量",
    features: [
      { name: "软著申请", single: "按次", starter: "10个", professional: "10个", enterprise: "100个", agency: "500个" },
      { name: "专利申请", single: false, starter: "支持", professional: "支持", enterprise: "支持", agency: "支持" },
      { name: "商标注册", single: false, starter: "支持", professional: "支持", enterprise: "支持", agency: "支持" },
    ],
  },
  {
    category: "存储与团队",
    features: [
      { name: "存储空间", single: "500MB", starter: "1GB", professional: "10GB", enterprise: "100GB", agency: "1TB" },
      { name: "团队成员", single: "1人", starter: "1人", professional: "3人", enterprise: "无限", agency: "20人" },
      { name: "团队协作", single: false, starter: false, professional: true, enterprise: true, agency: true },
    ],
  },
  {
    category: "核心功能",
    features: [
      { name: "代码自动处理", single: "基础", starter: "高级", professional: "高级", enterprise: "高级", agency: "高级" },
      { name: "AI说明书生成", single: false, starter: true, professional: true, enterprise: true, agency: true },
      { name: "合规检查", single: true, starter: true, professional: true, enterprise: true, agency: true },
      { name: "批量导出", single: false, starter: false, professional: true, enterprise: true, agency: true },
    ],
  },
  {
    category: "支持服务",
    features: [
      { name: "社区支持", single: true, starter: true, professional: true, enterprise: true, agency: true },
      { name: "邮件支持", single: false, starter: true, professional: true, enterprise: true, agency: true },
      { name: "优先支持", single: false, starter: false, professional: true, enterprise: true, agency: true },
      { name: "专属客户经理", single: false, starter: false, professional: false, enterprise: true, agency: true },
      { name: "SLA保障", single: false, starter: false, professional: false, enterprise: true, agency: true },
    ],
  },
  {
    category: "企业功能",
    features: [
      { name: "API访问", single: false, starter: false, professional: false, enterprise: "可选", agency: true },
      { name: "白标定制", single: false, starter: false, professional: false, enterprise: "可选", agency: true },
      { name: "私有化部署", single: false, starter: false, professional: false, enterprise: "可选", agency: false },
    ],
  },
];

const renderValue = (value: boolean | string) => {
  if (typeof value === "boolean") {
    return value ? (
      <Check className="h-5 w-5 text-green-500" />
    ) : (
      <X className="h-5 w-5 text-muted-foreground/30" />
    );
  }
  return <span className="text-sm">{value}</span>;
};

export function PlanComparison() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-2xl md:text-3xl font-bold mb-2">功能对比</h2>
        <p className="text-muted-foreground">选择最适合您的计划</p>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">功能</TableHead>
              <TableHead className="text-center">
                <div className="space-y-1">
                  <div className="font-bold">按次付费</div>
                  <div className="text-sm text-muted-foreground">¥19.0/次</div>
                </div>
              </TableHead>
              <TableHead className="text-center bg-blue-500/10">
                <div className="space-y-1">
                  <div className="font-bold">基础版</div>
                  <div className="text-sm text-muted-foreground">¥49/月</div>
                </div>
              </TableHead>
              <TableHead className="text-center">
                <div className="space-y-1">
                  <div className="font-bold">专业版</div>
                  <div className="text-sm text-muted-foreground">¥199/月</div>
                </div>
              </TableHead>
              <TableHead className="text-center">
                <div className="space-y-1">
                  <div className="font-bold">企业版</div>
                  <div className="text-sm text-muted-foreground">¥999/月</div>
                </div>
              </TableHead>
              <TableHead className="text-center">
                <div className="space-y-1">
                  <div className="font-bold">代理机构版</div>
                  <div className="text-sm text-muted-foreground">¥1999/月</div>
                </div>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {comparisonFeatures.map((group) => (
              <>
                <TableRow key={group.category} className="bg-muted/50">
                  <TableCell colSpan={6} className="font-bold">
                    {group.category}
                  </TableCell>
                </TableRow>
                {group.features.map((feature, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{feature.name}</TableCell>
                    <TableCell className="text-center">
                      {renderValue(feature.single)}
                    </TableCell>
                    <TableCell className="text-center">
                      {renderValue(feature.starter)}
                    </TableCell>
                    <TableCell className="text-center">
                      {renderValue(feature.professional)}
                    </TableCell>
                    <TableCell className="text-center">
                      {renderValue(feature.enterprise)}
                    </TableCell>
                    <TableCell className="text-center">
                      {renderValue(feature.agency)}
                    </TableCell>
                  </TableRow>
                ))}
              </>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
