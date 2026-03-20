"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/page-header";
import { FileCode, Lightbulb, Stamp, CheckCircle } from "lucide-react";

const rules = [
  {
    type: "copyright",
    title: "软件著作权申请规范",
    icon: FileCode,
    items: [
      "软件名称应当简洁明了，体现软件功能特点",
      "版本号格式建议为 V1.0 或 1.0.0 格式",
      "源代码需提供前后各 30 页，每页 50 行",
      "文档应当包含软件功能说明和技术特点",
    ],
  },
  {
    type: "patent",
    title: "专利申请规范",
    icon: Lightbulb,
    items: [
      "发明名称应当简短、准确地表明主题",
      "技术领域应当明确所属技术领域",
      "背景技术应当说明现有技术存在的问题",
      "发明内容应当清楚、完整地描述技术方案",
    ],
  },
  {
    type: "trademark",
    title: "商标申请规范",
    icon: Stamp,
    items: [
      "商标图样应当清晰、便于粘贴",
      "商品/服务类别应当按照尼斯分类填写",
      "申请人名义应当与营业执照一致",
      "委托书应当加盖公章或签字",
    ],
  },
];

export default function RulesPage() {
  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="申请规范"
        description="各类知识产权申请的规范和注意事项"
      />

      <div className="grid gap-6">
        {rules.map((rule) => (
          <Card key={rule.type}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <rule.icon className="h-5 w-5" />
                {rule.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {rule.items.map((item, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 mt-0.5 text-primary shrink-0" />
                    <span className="text-sm text-muted-foreground">{item}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
