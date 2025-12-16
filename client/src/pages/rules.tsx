import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  FileCode,
  FileText,
  Shield,
  CheckCircle,
  Info,
} from "lucide-react";

const codeRules = [
  {
    id: "pages",
    name: "页数要求",
    requirement: "共 60 页（前30页 + 后30页）",
    description: "若源代码不足60页则全量提交",
    important: true,
  },
  {
    id: "lines",
    name: "每页行数",
    requirement: "不少于 50 行（去除空行）",
    description: "去除空行后计算有效行数",
    important: true,
  },
  {
    id: "header",
    name: "页眉格式",
    requirement: "软件全称 + 版本号",
    description: "例如：智能办公管理系统软件 V1.0",
    important: true,
  },
  {
    id: "lineNumber",
    name: "行号要求",
    requirement: "自动添加连续行号",
    description: "行号从1开始连续编号",
    important: false,
  },
  {
    id: "font",
    name: "字体要求",
    requirement: "等宽字体",
    description: "推荐使用 Consolas 或 JetBrains Mono",
    important: false,
  },
  {
    id: "pageNumber",
    name: "页码要求",
    requirement: "1-60 连续页码",
    description: "底部居中显示页码",
    important: false,
  },
];

const manualRules = [
  {
    id: "minPages",
    name: "最少页数",
    requirement: "不少于 15 页",
    description: "图文并茂的完整说明书",
    important: true,
  },
  {
    id: "lines",
    name: "每页行数",
    requirement: "不少于 30 行",
    description: "包含文字和图片说明",
    important: true,
  },
  {
    id: "toc",
    name: "目录结构",
    requirement: "自动生成目录",
    description: "章节层级清晰，页码准确",
    important: true,
  },
  {
    id: "screenshots",
    name: "界面截图",
    requirement: "图文并茂",
    description: "功能点配套截图说明",
    important: false,
  },
  {
    id: "extractRule",
    name: "抽取规则",
    requirement: "≥60页时抽取前30+后30",
    description: "不足60页则全量提交",
    important: false,
  },
];

const proofRules = [
  {
    id: "identity",
    name: "身份证明",
    requirement: "必须提交",
    description: "自然人提供身份证复印件，法人提供营业执照",
    important: true,
    condition: "所有申请",
  },
  {
    id: "contract",
    name: "合同/任务书",
    requirement: "按需提交",
    description: "委托开发、合作开发时需要",
    important: false,
    condition: "委托/合作开发",
  },
  {
    id: "license",
    name: "许可证明",
    requirement: "按需提交",
    description: "二次开发、改编时需要原软件权利人许可",
    important: false,
    condition: "二次开发/改编",
  },
  {
    id: "inheritance",
    name: "继承/受让证明",
    requirement: "按需提交",
    description: "通过继承或转让获得权利时需要",
    important: false,
    condition: "继承/受让",
  },
];

export default function RulesPage() {
  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="合规规则"
        description="软著申请材料的格式要求与规范说明"
      />

      <Tabs defaultValue="code" className="space-y-6">
        <TabsList>
          <TabsTrigger value="code" className="gap-2">
            <FileCode className="h-4 w-4" />
            源代码
          </TabsTrigger>
          <TabsTrigger value="manual" className="gap-2">
            <FileText className="h-4 w-4" />
            说明书
          </TabsTrigger>
          <TabsTrigger value="proof" className="gap-2">
            <Shield className="h-4 w-4" />
            证明材料
          </TabsTrigger>
        </TabsList>

        <TabsContent value="code" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>源代码鉴别材料规范</CardTitle>
              <CardDescription>
                按照国家版权局要求，源代码材料需满足以下格式要求
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {codeRules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-start gap-3 p-4 rounded-md border"
                  >
                    <CheckCircle
                      className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
                        rule.important
                          ? "text-primary"
                          : "text-muted-foreground"
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{rule.name}</span>
                        {rule.important && (
                          <Badge variant="secondary" className="text-xs">
                            必须
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-primary font-medium mt-1">
                        {rule.requirement}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {rule.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                代码抽取策略
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm text-muted-foreground space-y-2">
                <p>• 主语言优先：抽取项目主要编程语言的代码文件</p>
                <p>• 排除生成目录：自动跳过 node_modules、dist、build 等目录</p>
                <p>• 保留核心逻辑：优先保留业务核心代码，而非配置文件</p>
                <p>• 去除注释空行：计算有效代码行数时不计入纯注释行和空行</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manual" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>操作说明书规范</CardTitle>
              <CardDescription>
                说明书需完整描述软件的功能和使用方法
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {manualRules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-start gap-3 p-4 rounded-md border"
                  >
                    <CheckCircle
                      className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
                        rule.important
                          ? "text-primary"
                          : "text-muted-foreground"
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{rule.name}</span>
                        {rule.important && (
                          <Badge variant="secondary" className="text-xs">
                            必须
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-primary font-medium mt-1">
                        {rule.requirement}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {rule.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>说明书章节建议</CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="w-full">
                {[
                  {
                    title: "1. 摘要与版本信息",
                    content: "软件名称、版本、开发单位、完成日期等基本信息",
                  },
                  {
                    title: "2. 系统概述",
                    content: "系统目标、面向用户、功能边界、技术架构概述",
                  },
                  {
                    title: "3. 安装与运行环境",
                    content: "硬件要求、操作系统、依赖软件、安装步骤",
                  },
                  {
                    title: "4. 功能说明",
                    content:
                      "按模块逐一说明功能点，配套界面截图和操作步骤",
                  },
                  {
                    title: "5. 数据结构/接口",
                    content: "数据库设计、API接口定义（如适用）",
                  },
                  {
                    title: "6. 权限与日志",
                    content: "用户角色、权限控制、日志记录说明",
                  },
                  {
                    title: "7. 典型业务流程",
                    content: "使用流程图、泳道图展示主要业务流程",
                  },
                  {
                    title: "8. 性能与限制",
                    content: "性能指标、已知限制、注意事项",
                  },
                  {
                    title: "9. 版本更新记录",
                    content: "版本历史、主要更新内容",
                  },
                  {
                    title: "10. 版权与声明",
                    content: "版权声明、法律责任说明",
                  },
                ].map((item, index) => (
                  <AccordionItem key={index} value={`item-${index}`}>
                    <AccordionTrigger className="text-sm">
                      {item.title}
                    </AccordionTrigger>
                    <AccordionContent className="text-sm text-muted-foreground">
                      {item.content}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="proof" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>证明材料清单</CardTitle>
              <CardDescription>
                根据申请类型和开发方式，系统将自动提示所需证明材料
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {proofRules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-start gap-3 p-4 rounded-md border"
                  >
                    <Shield
                      className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
                        rule.important
                          ? "text-primary"
                          : "text-muted-foreground"
                      }`}
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between gap-4 flex-wrap">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{rule.name}</span>
                          <Badge
                            variant={rule.important ? "default" : "outline"}
                            className="text-xs"
                          >
                            {rule.requirement}
                          </Badge>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {rule.condition}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {rule.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                材料格式要求
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground space-y-2">
                <p>• 统一使用 A4 纸张 (297mm × 210mm)</p>
                <p>• 所有材料使用中文填写</p>
                <p>• 扫描件需清晰可辨，分辨率不低于 300dpi</p>
                <p>• 签章位置预留在页面底部指定区域</p>
                <p>• 提交文件需留存副本备查</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
