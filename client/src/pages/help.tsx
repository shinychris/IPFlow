import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  HelpCircle,
  BookOpen,
  MessageCircle,
  Lightbulb,
  CheckCircle,
  AlertCircle,
  FileCode,
  Stamp,
} from "lucide-react";

interface FaqItem {
  question: string;
  answer: string;
}

const copyrightFaq: FaqItem[] = [
  {
    question: "什么是软件著作权？",
    answer: "软件著作权是指软件的开发者或者其他权利人依据有关著作权法律的规定，对于软件作品所享有的各项专有权利。软著登记是版权保护的重要方式，也是高新技术企业认定、双软认证的必要条件。",
  },
  {
    question: "软著申请需要多长时间？",
    answer: "一般情况下，软著登记需要30-60个工作日。使用本工具可以在1天内完成材料准备，大大缩短整体申请周期。如果选择加急服务，审批时间可缩短至3-10个工作日。",
  },
  {
    question: "源代码需要提交全部吗？",
    answer: "不需要。按照规定，源代码材料只需提交前30页和后30页（共60页），每页不少于50行有效代码。如果代码不足60页，则全量提交。本工具会自动按规则抽取并格式化。",
  },
  {
    question: "操作说明书有什么要求？",
    answer: "说明书需不少于15页，每页不少于30行，图文并茂地说明软件的功能和使用方法。需包含软件概述、安装说明、功能描述、操作步骤等章节。本工具提供5种类型的模板供选择。",
  },
  {
    question: "个人和企业申请有什么区别？",
    answer: "主要区别在于身份证明材料：个人需提供身份证复印件，企业需提供营业执照副本复印件。另外，企业申请时如果是委托或合作开发，还需要提供相应的合同或协议。",
  },
  {
    question: "什么情况需要提供合同/任务书？",
    answer: "当开发方式选择「委托开发」或「合作开发」时，需要提供委托合同或合作开发协议，明确软件著作权的归属。如果是职务作品，可能需要提供任务书或立项书。",
  },
  {
    question: "二次开发需要什么额外材料？",
    answer: "二次开发或改编他人软件时，需要提供原软件著作权人的书面许可证明，明确授权进行二次开发并允许登记新的著作权。",
  },
  {
    question: "软件版本号怎么填写？",
    answer: "版本号通常采用 V1.0、V2.0 格式，或 V1.0.0 格式。首次申请建议使用 V1.0。如果是升级版本，需与原版本有实质性区别（如功能增加、架构调整等）。",
  },
];

const patentFaq: FaqItem[] = [
  {
    question: "发明专利和实用新型有什么区别？",
    answer: "发明专利保护产品和方法，审查周期较长（通常2-3年），保护期20年。实用新型仅保护产品的形状和结构，审查快（通常6-12个月），保护期10年。发明专利需经过实质审查，实用新型仅初步审查。",
  },
  {
    question: "专利申请的基本流程是什么？",
    answer: "一般流程为：技术交底 → 检索分析 → 撰写申请文件（权利要求书、说明书、摘要等） → 提交申请 → 受理 → 初步审查 → 实质审查（发明专利）→ 授权公告。本工具帮助您快速完成申请文件的撰写。",
  },
  {
    question: "权利要求书怎么撰写？",
    answer: "权利要求书包括独立权利要求和从属权利要求。独立权利要求应包含前序部分（现有技术）和特征部分（创新点），用「其特征在于」连接。从属权利要求引用在前权利要求，附加更具体的技术特征。",
  },
  {
    question: "说明书需要包含哪些内容？",
    answer: "说明书应包含：技术领域、背景技术、发明内容（技术问题、技术方案、有益效果）、附图说明、具体实施方式。每个部分都需要详细且清晰的描述。",
  },
  {
    question: "摘要有什么要求？",
    answer: "摘要应概述发明的技术方案要点和主要用途，不超过300字。摘要附图应选择最能反映技术方案的附图。摘要不具有法律效力，仅用于技术情报检索。",
  },
  {
    question: "什么是优先权？",
    answer: "优先权是指申请人在一个国家首次提出专利申请后，在规定期限内（发明和实用新型12个月，外观设计6个月）向其他国家申请时，可以享有首次申请日的优先权。需提供优先权证明文件。",
  },
  {
    question: "专利申请费用是多少？",
    answer: "官方费用包括申请费（发明900元、实用新型500元、外观500元）、实质审查费（发明2500元）、授权登记费等。个人或小微企业可申请费用减缴（减缴85%）。代理费另计。",
  },
];

const trademarkFaq: FaqItem[] = [
  {
    question: "什么是商标注册？",
    answer: "商标注册是指商标所有人为获得商标专用权，将其使用的商标向商标局申请注册。注册商标受法律保护，未经注册也可使用商标，但不受法律保护，且可能侵犯他人的注册商标权。",
  },
  {
    question: "商标注册需要多长时间？",
    answer: "一般审查周期为9-12个月，包括形式审查（约1个月）、实质审查（约6-8个月）、初审公告（3个月异议期）。如无异议，公告期满后颁发注册证。",
  },
  {
    question: "什么是尼斯分类？",
    answer: "尼斯分类是商品和服务的国际分类体系，共45个类别（1-34类为商品，35-45类为服务）。申请人需按照经营范围选择对应的类别和具体商品/服务项目。不同类别需分别申请。",
  },
  {
    question: "商标图样有什么要求？",
    answer: "商标图样应当清晰，尺寸为5cm×5cm至10cm×10cm。指定颜色的须提交彩色图样，并注明颜色。黑白图样不指定颜色的，可在任何颜色上使用。",
  },
  {
    question: "如何选择商品/服务类别？",
    answer: "应根据实际经营范围和未来规划选择。IT/互联网企业通常选择第9类（软件）、第35类（电商/广告）、第38类（通讯）、第42类（技术服务）等。建议同时注册相关类别进行防御性保护。",
  },
  {
    question: "商标驳回了怎么办？",
    answer: "收到驳回通知后，可在15日内向商标评审委员会提出复审。复审应提供充分的使用证据和理由。如果因近似商标被驳回，可考虑修改图样或更换名称重新申请。",
  },
  {
    question: "商标有效期是多久？",
    answer: "注册商标有效期为10年，自核准注册之日起计算。期满前12个月内可申请续展，每次续展有效期10年。未按时续展的，有6个月的宽展期。",
  },
  {
    question: "个人可以申请商标吗？",
    answer: "可以，但个人申请需提供个体工商户营业执照，且商标使用范围限于营业执照核准的经营范围。纯自然人（无营业执照）不能申请商标注册。",
  },
];

const copyrightSteps = [
  { step: 1, title: "创建项目", description: "选择主体类型、开发方式、发表状态，填写项目基本信息" },
  { step: 2, title: "填写软件信息", description: "完善软件全称、版本号、开发语言、功能描述等详细信息" },
  { step: 3, title: "上传源代码", description: "上传代码压缩包，系统自动抽取并生成符合规范的60页代码材料" },
  { step: 4, title: "编写说明书", description: "选择模板，编写操作说明书，插入截图，生成目录和页码" },
  { step: 5, title: "导出打包", description: "完成合规检查，导出完整的软著申请材料包，准备提交" },
];

const patentSteps = [
  { step: 1, title: "创建项目", description: "选择专利类型（发明/实用新型/外观设计），填写基本信息" },
  { step: 2, title: "填写专利信息", description: "填写发明名称、摘要、申请人和发明人信息" },
  { step: 3, title: "撰写权利要求", description: "编写独立权利要求和从属权利要求，确定保护范围" },
  { step: 4, title: "撰写说明书", description: "编写技术领域、背景技术、技术方案、有益效果等内容" },
  { step: 5, title: "导出打包", description: "完成合规检查，导出完整的专利申请材料包" },
];

const trademarkSteps = [
  { step: 1, title: "创建项目", description: "选择商标类型，填写项目基本信息" },
  { step: 2, title: "填写商标信息", description: "填写商标名称、申请人信息、上传商标图样" },
  { step: 3, title: "选择商品服务", description: "根据尼斯分类选择商品/服务类别和具体项目" },
  { step: 4, title: "导出打包", description: "完成合规检查，导出完整的商标申请材料包" },
];

const tips = [
  { title: "软件名称规范", content: "软著申请时，软件名称建议以「系统」、「平台」、「软件」、「APP」等结尾", type: "info" },
  { title: "确保一致性", content: "各类申请中，名称和版本号在所有材料中必须完全一致", type: "warning" },
  { title: "保留备份", content: "提交前务必保存电子版和纸质版各一份，以备后续使用", type: "info" },
  { title: "提前检索", content: "专利和商标申请前，建议先进行检索查重，避免因重复而被驳回", type: "warning" },
  { title: "分类策略", content: "商标申请时，建议在核心类别和关联类别同时注册，进行防御性保护", type: "info" },
  { title: "时效注意", content: "各类申请都有时效要求，尽早提交可避免被他人抢先", type: "warning" },
];

function FlowSteps({ steps }: { steps: { step: number; title: string; description: string }[] }) {
  return (
    <div className="space-y-4">
      {steps.map((item) => (
        <div key={item.step} className="flex gap-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground font-medium text-sm flex-shrink-0">
            {item.step}
          </div>
          <div>
            <div className="font-medium">{item.title}</div>
            <div className="text-sm text-muted-foreground">{item.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function FaqAccordion({ items }: { items: FaqItem[] }) {
  return (
    <Accordion type="single" collapsible className="w-full">
      {items.map((item, index) => (
        <AccordionItem key={index} value={`faq-${index}`}>
          <AccordionTrigger className="text-left">{item.question}</AccordionTrigger>
          <AccordionContent className="text-muted-foreground">{item.answer}</AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}

export default function HelpPage() {
  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      <PageHeader
        title="帮助文档"
        description="知识产权申请常见问题解答与使用指南"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="copyright" className="space-y-6">
            <TabsList>
              <TabsTrigger value="copyright" className="gap-2" data-testid="tab-help-copyright">
                <FileCode className="h-4 w-4" />
                软著申请
              </TabsTrigger>
              <TabsTrigger value="patent" className="gap-2" data-testid="tab-help-patent">
                <Lightbulb className="h-4 w-4" />
                专利申请
              </TabsTrigger>
              <TabsTrigger value="trademark" className="gap-2" data-testid="tab-help-trademark">
                <Stamp className="h-4 w-4" />
                商标申请
              </TabsTrigger>
            </TabsList>

            <TabsContent value="copyright" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HelpCircle className="h-5 w-5" />
                    软著申请常见问题
                  </CardTitle>
                  <CardDescription>关于计算机软件著作权登记的常见问题</CardDescription>
                </CardHeader>
                <CardContent>
                  <FaqAccordion items={copyrightFaq} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    软著申请流程
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FlowSteps steps={copyrightSteps} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="patent" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HelpCircle className="h-5 w-5" />
                    专利申请常见问题
                  </CardTitle>
                  <CardDescription>关于发明专利、实用新型、外观设计的常见问题</CardDescription>
                </CardHeader>
                <CardContent>
                  <FaqAccordion items={patentFaq} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    专利申请流程
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FlowSteps steps={patentSteps} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="trademark" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HelpCircle className="h-5 w-5" />
                    商标申请常见问题
                  </CardTitle>
                  <CardDescription>关于商标注册申请的常见问题</CardDescription>
                </CardHeader>
                <CardContent>
                  <FaqAccordion items={trademarkFaq} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    商标申请流程
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FlowSteps steps={trademarkSteps} />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
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
                  data-testid={`tip-${index}`}
                >
                  {tip.type === "warning" ? (
                    <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="font-medium text-sm">{tip.title}</div>
                    <div className="text-sm text-muted-foreground">{tip.content}</div>
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
