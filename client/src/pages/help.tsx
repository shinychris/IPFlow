import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import {
  HelpCircle,
  BookOpen,
  MessageCircle,
  Lightbulb,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

const faqItems = [
  {
    question: "什么是软件著作权？",
    answer:
      "软件著作权是指软件的开发者或者其他权利人依据有关著作权法律的规定，对于软件作品所享有的各项专有权利。软著登记是版权保护的重要方式，也是高新技术企业认定、双软认证的必要条件。",
  },
  {
    question: "软著申请需要多长时间？",
    answer:
      "一般情况下，软著登记需要30-60个工作日。使用本工具可以在1天内完成材料准备，大大缩短整体申请周期。如果选择加急服务，审批时间可缩短至3-10个工作日。",
  },
  {
    question: "源代码需要提交全部吗？",
    answer:
      "不需要。按照规定，源代码材料只需提交前30页和后30页（共60页），每页不少于50行有效代码。如果代码不足60页，则全量提交。本工具会自动按规则抽取并格式化。",
  },
  {
    question: "操作说明书有什么要求？",
    answer:
      "说明书需不少于15页，每页不少于30行，图文并茂地说明软件的功能和使用方法。需包含软件概述、安装说明、功能描述、操作步骤等章节。本工具提供5种类型的模板供选择。",
  },
  {
    question: "个人和企业申请有什么区别？",
    answer:
      "主要区别在于身份证明材料：个人需提供身份证复印件，企业需提供营业执照副本复印件。另外，企业申请时如果是委托或合作开发，还需要提供相应的合同或协议。",
  },
  {
    question: "什么情况需要提供合同/任务书？",
    answer:
      "当开发方式选择「委托开发」或「合作开发」时，需要提供委托合同或合作开发协议，明确软件著作权的归属。如果是职务作品，可能需要提供任务书或立项书。",
  },
  {
    question: "二次开发需要什么额外材料？",
    answer:
      "二次开发或改编他人软件时，需要提供原软件著作权人的书面许可证明，明确授权进行二次开发并允许登记新的著作权。",
  },
  {
    question: "软件版本号怎么填写？",
    answer:
      "版本号通常采用 V1.0、V2.0 格式，或 V1.0.0 格式。首次申请建议使用 V1.0。如果是升级版本，需与原版本有实质性区别（如功能增加、架构调整等）。",
  },
];

const tips = [
  {
    title: "软件名称规范",
    content: "建议以「系统」、「平台」、「软件」、「APP」等结尾，如「智能办公管理系统软件」",
    type: "info",
  },
  {
    title: "确保一致性",
    content: "软件名称、版本号在申请表、代码页眉、说明书中必须完全一致",
    type: "warning",
  },
  {
    title: "保留备份",
    content: "提交前务必保存电子版和纸质版各一份，以备后续使用",
    type: "info",
  },
  {
    title: "避免敏感词",
    content: "软件名称中避免使用「中国」、「国家」等敏感词汇，可能导致审核不通过",
    type: "warning",
  },
];

export default function HelpPage() {
  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="帮助文档"
        description="软著申请常见问题解答与使用指南"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HelpCircle className="h-5 w-5" />
                常见问题
              </CardTitle>
              <CardDescription>
                关于软著申请的常见问题解答
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {faqItems.map((item, index) => (
                  <AccordionItem key={index} value={`faq-${index}`}>
                    <AccordionTrigger className="text-left">
                      {item.question}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground">
                      {item.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                申请流程指南
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    step: 1,
                    title: "创建项目",
                    description: "选择主体类型、开发方式、发表状态，填写项目基本信息",
                  },
                  {
                    step: 2,
                    title: "填写软件信息",
                    description:
                      "完善软件全称、版本号、开发语言、功能描述等详细信息",
                  },
                  {
                    step: 3,
                    title: "上传源代码",
                    description:
                      "上传代码压缩包，系统自动抽取并生成符合规范的60页代码材料",
                  },
                  {
                    step: 4,
                    title: "编写说明书",
                    description:
                      "选择模板，编写操作说明书，插入截图，生成目录和页码",
                  },
                  {
                    step: 5,
                    title: "导出打包",
                    description:
                      "完成合规检查，导出完整的软著申请材料包，准备提交",
                  },
                ].map((item) => (
                  <div key={item.step} className="flex gap-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground font-medium text-sm flex-shrink-0">
                      {item.step}
                    </div>
                    <div>
                      <div className="font-medium">{item.title}</div>
                      <div className="text-sm text-muted-foreground">
                        {item.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Lightbulb className="h-5 w-5" />
                实用提示
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {tips.map((tip, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-md border"
                >
                  {tip.type === "warning" ? (
                    <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="font-medium text-sm">{tip.title}</div>
                    <div className="text-sm text-muted-foreground">
                      {tip.content}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <MessageCircle className="h-5 w-5" />
                联系支持
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-3">
              <p>如有其他问题，欢迎通过以下方式联系我们：</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 rounded-md bg-muted">
                  <span>在线客服</span>
                  <Badge variant="secondary">工作日 9:00-18:00</Badge>
                </div>
                <div className="flex items-center justify-between p-2 rounded-md bg-muted">
                  <span>邮箱反馈</span>
                  <span className="text-primary">support@example.com</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
