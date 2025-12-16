import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Globe,
  Smartphone,
  Code,
  Terminal,
  Monitor,
  Download,
  Eye,
} from "lucide-react";
import { templateTypeLabels, type TemplateType } from "@shared/schema";

const templateIcons: Record<TemplateType, typeof Globe> = {
  web: Globe,
  mobile: Smartphone,
  algorithm: Code,
  script: Terminal,
  desktop: Monitor,
};

const templateDescriptions: Record<TemplateType, string> = {
  web: "适用于网站、Web应用、SaaS平台等",
  mobile: "适用于iOS、Android移动应用",
  algorithm: "适用于算法库、SDK、API服务",
  script: "适用于脚本工具、命令行程序",
  desktop: "适用于Windows、Mac桌面软件",
};

const templates: Array<{
  type: TemplateType;
  sections: number;
  estimatedPages: string;
  features: string[];
}> = [
  {
    type: "web",
    sections: 10,
    estimatedPages: "15-30",
    features: ["界面截图示例", "功能模块说明", "API接口文档"],
  },
  {
    type: "mobile",
    sections: 10,
    estimatedPages: "15-25",
    features: ["App界面截图", "手势操作说明", "推送通知说明"],
  },
  {
    type: "algorithm",
    sections: 8,
    estimatedPages: "15-20",
    features: ["算法流程图", "接口定义", "性能指标"],
  },
  {
    type: "script",
    sections: 6,
    estimatedPages: "10-15",
    features: ["命令参数说明", "配置文件格式", "使用示例"],
  },
  {
    type: "desktop",
    sections: 10,
    estimatedPages: "20-35",
    features: ["安装向导", "菜单功能", "快捷键说明"],
  },
];

export default function TemplatesPage() {
  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="模板库"
        description="选择适合您软件类型的操作说明书模板"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {templates.map((template) => {
          const Icon = templateIcons[template.type];
          return (
            <Card
              key={template.type}
              className="hover-elevate transition-all"
              data-testid={`card-template-${template.type}`}
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <Badge variant="secondary">{template.sections} 章节</Badge>
                </div>
                <CardTitle className="mt-4">
                  {templateTypeLabels[template.type]}
                </CardTitle>
                <CardDescription>
                  {templateDescriptions[template.type]}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  预计页数：{template.estimatedPages} 页
                </div>

                <div className="space-y-2">
                  <div className="text-sm font-medium">模板特色</div>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {template.features.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    data-testid={`button-preview-${template.type}`}
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    预览
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1"
                    data-testid={`button-use-${template.type}`}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    使用
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            法律文书模板
          </CardTitle>
          <CardDescription>
            根据开发方式自动匹配所需的法律文书模板
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {[
              { name: "授权委托书", description: "个人/企业授权代理人办理" },
              { name: "合作开发协议", description: "多方合作开发权利分配" },
              { name: "任务书/立项书", description: "用于权属证明" },
              { name: "许可证明", description: "二次开发/改编许可" },
            ].map((doc) => (
              <div
                key={doc.name}
                className="flex items-start gap-3 p-4 rounded-md border hover-elevate cursor-pointer"
              >
                <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-medium">{doc.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {doc.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
