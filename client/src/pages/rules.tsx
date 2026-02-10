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
  Lightbulb,
  Stamp,
} from "lucide-react";

interface Rule {
  id: string;
  name: string;
  requirement: string;
  description: string;
  important: boolean;
  condition?: string;
}

function RuleGrid({ rules }: { rules: Rule[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {rules.map((rule) => (
        <div
          key={rule.id}
          className="flex items-start gap-3 p-4 rounded-md border"
          data-testid={`rule-${rule.id}`}
        >
          <CheckCircle
            className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
              rule.important ? "text-primary" : "text-muted-foreground"
            }`}
          />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium">{rule.name}</span>
              {rule.important && (
                <Badge variant="secondary" className="text-xs">必须</Badge>
              )}
            </div>
            <div className="text-sm text-primary font-medium mt-1">{rule.requirement}</div>
            <div className="text-sm text-muted-foreground">{rule.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ProofRuleList({ rules }: { rules: Rule[] }) {
  return (
    <div className="space-y-4">
      {rules.map((rule) => (
        <div
          key={rule.id}
          className="flex items-start gap-3 p-4 rounded-md border"
          data-testid={`proof-rule-${rule.id}`}
        >
          <Shield
            className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
              rule.important ? "text-primary" : "text-muted-foreground"
            }`}
          />
          <div className="flex-1">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <span className="font-medium">{rule.name}</span>
                <Badge variant={rule.important ? "default" : "outline"} className="text-xs">
                  {rule.requirement}
                </Badge>
              </div>
              {rule.condition && (
                <Badge variant="secondary" className="text-xs">{rule.condition}</Badge>
              )}
            </div>
            <div className="text-sm text-muted-foreground mt-1">{rule.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

const copyrightCodeRules: Rule[] = [
  { id: "cr-pages", name: "页数要求", requirement: "共 60 页（前30页 + 后30页）", description: "若源代码不足60页则全量提交", important: true },
  { id: "cr-lines", name: "每页行数", requirement: "不少于 50 行（去除空行）", description: "去除空行后计算有效行数", important: true },
  { id: "cr-header", name: "页眉格式", requirement: "软件全称 + 版本号", description: "例如：智能办公管理系统软件 V1.0", important: true },
  { id: "cr-linenum", name: "行号要求", requirement: "自动添加连续行号", description: "行号从1开始连续编号", important: false },
  { id: "cr-font", name: "字体要求", requirement: "等宽字体", description: "推荐使用 Consolas 或 JetBrains Mono", important: false },
  { id: "cr-pagenum", name: "页码要求", requirement: "1-60 连续页码", description: "底部居中显示页码", important: false },
];

const copyrightManualRules: Rule[] = [
  { id: "cm-minpages", name: "最少页数", requirement: "不少于 15 页", description: "图文并茂的完整说明书", important: true },
  { id: "cm-lines", name: "每页行数", requirement: "不少于 30 行", description: "包含文字和图片说明", important: true },
  { id: "cm-toc", name: "目录结构", requirement: "自动生成目录", description: "章节层级清晰，页码准确", important: true },
  { id: "cm-screenshot", name: "界面截图", requirement: "图文并茂", description: "功能点配套截图说明", important: false },
  { id: "cm-extract", name: "抽取规则", requirement: "≥60页时抽取前30+后30", description: "不足60页则全量提交", important: false },
];

const copyrightProofRules: Rule[] = [
  { id: "cp-identity", name: "身份证明", requirement: "必须提交", description: "自然人提供身份证复印件，法人提供营业执照", important: true, condition: "所有申请" },
  { id: "cp-contract", name: "合同/任务书", requirement: "按需提交", description: "委托开发、合作开发时需要", important: false, condition: "委托/合作开发" },
  { id: "cp-license", name: "许可证明", requirement: "按需提交", description: "二次开发、改编时需要原软件权利人许可", important: false, condition: "二次开发/改编" },
  { id: "cp-inherit", name: "继承/受让证明", requirement: "按需提交", description: "通过继承或转让获得权利时需要", important: false, condition: "继承/受让" },
];

const patentInfoRules: Rule[] = [
  { id: "pt-title", name: "发明名称", requirement: "简明、准确", description: "不超过25个字，不得使用商业性宣传用语", important: true },
  { id: "pt-abstract", name: "摘要", requirement: "不超过 300 字", description: "概述发明的技术方案要点和主要用途", important: true },
  { id: "pt-applicant", name: "申请人信息", requirement: "准确完整", description: "申请人名称、地址需与身份证明一致", important: true },
  { id: "pt-inventor", name: "发明人信息", requirement: "真实姓名", description: "对发明创造有实质性贡献的自然人", important: true },
];

const patentClaimsRules: Rule[] = [
  { id: "pc-independent", name: "独立权利要求", requirement: "至少 1 项", description: "完整描述发明的技术方案", important: true },
  { id: "pc-dependent", name: "从属权利要求", requirement: "引用在前权利要求", description: "附加技术特征对引用的权利要求进一步限定", important: false },
  { id: "pc-format", name: "撰写格式", requirement: "前序部分 + 特征部分", description: "独立权要使用「其特征在于」连接两部分", important: true },
  { id: "pc-support", name: "说明书支持", requirement: "以说明书为依据", description: "每项权利要求都应有说明书的支持", important: true },
];

const patentDescriptionRules: Rule[] = [
  { id: "pd-field", name: "技术领域", requirement: "必须包含", description: "说明发明所属的技术领域", important: true },
  { id: "pd-background", name: "背景技术", requirement: "必须包含", description: "引用对比文件，说明现有技术的不足", important: true },
  { id: "pd-problem", name: "技术问题", requirement: "必须包含", description: "说明发明要解决的技术问题", important: true },
  { id: "pd-solution", name: "技术方案", requirement: "必须包含", description: "详细描述发明的技术方案", important: true },
  { id: "pd-effect", name: "有益效果", requirement: "必须包含", description: "说明发明的有益效果和优势", important: true },
  { id: "pd-drawings", name: "附图说明", requirement: "视情况而定", description: "发明专利一般需要附图；实用新型必须有附图", important: false },
  { id: "pd-example", name: "具体实施方式", requirement: "至少一个实施例", description: "详细描述发明的实施例", important: true },
];

const patentProofRules: Rule[] = [
  { id: "pp-identity", name: "身份证明", requirement: "必须提交", description: "申请人身份证明文件", important: true, condition: "所有申请" },
  { id: "pp-poa", name: "委托书", requirement: "委托代理时提交", description: "专利代理委托书", important: false, condition: "委托代理" },
  { id: "pp-priority", name: "优先权证明", requirement: "主张优先权时提交", description: "优先权文件副本", important: false, condition: "主张优先权" },
  { id: "pp-drawings", name: "附图文件", requirement: "按需提交", description: "符合专利局要求的附图格式", important: false, condition: "含附图" },
];

const trademarkInfoRules: Rule[] = [
  { id: "tm-name", name: "商标名称", requirement: "确定且唯一", description: "商标名称应具有显著性，不得与在先商标相同或近似", important: true },
  { id: "tm-type", name: "商标类型", requirement: "明确类型", description: "文字、图形、组合、三维、声音、颜色等", important: true },
  { id: "tm-applicant", name: "申请人信息", requirement: "准确完整", description: "申请人名称和地址需与身份证明一致", important: true },
  { id: "tm-contact", name: "联系信息", requirement: "有效联系方式", description: "联系人、电话、邮箱等", important: false },
];

const trademarkImageRules: Rule[] = [
  { id: "ti-format", name: "图样格式", requirement: "JPG/PNG 格式", description: "清晰的商标图样文件", important: true },
  { id: "ti-size", name: "图样尺寸", requirement: "5cm×5cm 至 10cm×10cm", description: "提交的图样尺寸需在规定范围内", important: true },
  { id: "ti-color", name: "颜色声明", requirement: "按需声明", description: "指定颜色的商标须提交彩色图样并声明颜色", important: false },
  { id: "ti-description", name: "商标描述", requirement: "按需提交", description: "三维、声音等特殊类型需文字描述", important: false },
];

const trademarkClassRules: Rule[] = [
  { id: "tc-nice", name: "尼斯分类", requirement: "至少选择 1 个类别", description: "根据《类似商品和服务区分表》选择", important: true },
  { id: "tc-items", name: "商品/服务项目", requirement: "每类至少 1 项", description: "从所选类别中选择具体商品或服务项目", important: true },
  { id: "tc-cross", name: "交叉检索", requirement: "建议进行", description: "注意跨类别的类似商品或服务", important: false },
  { id: "tc-strategy", name: "防御性注册", requirement: "建议考虑", description: "考虑相关类别的防御性注册，避免恶意抢注", important: false },
];

const trademarkProofRules: Rule[] = [
  { id: "tp-identity", name: "身份证明", requirement: "必须提交", description: "申请人身份证明文件", important: true, condition: "所有申请" },
  { id: "tp-image", name: "商标图样", requirement: "必须提交", description: "清晰的商标图样文件", important: true, condition: "所有申请" },
  { id: "tp-poa", name: "委托书", requirement: "委托代理时提交", description: "商标代理委托书", important: false, condition: "委托代理" },
  { id: "tp-priority", name: "优先权证明", requirement: "主张优先权时提交", description: "优先权证明文件", important: false, condition: "主张优先权" },
  { id: "tp-evidence", name: "使用证据", requirement: "按需提交", description: "商标已投入使用的证据", important: false, condition: "已使用商标" },
];

const manualChapters = [
  { title: "1. 摘要与版本信息", content: "软件名称、版本、开发单位、完成日期等基本信息" },
  { title: "2. 系统概述", content: "系统目标、面向用户、功能边界、技术架构概述" },
  { title: "3. 安装与运行环境", content: "硬件要求、操作系统、依赖软件、安装步骤" },
  { title: "4. 功能说明", content: "按模块逐一说明功能点，配套界面截图和操作步骤" },
  { title: "5. 数据结构/接口", content: "数据库设计、API接口定义（如适用）" },
  { title: "6. 权限与日志", content: "用户角色、权限控制、日志记录说明" },
  { title: "7. 典型业务流程", content: "使用流程图、泳道图展示主要业务流程" },
  { title: "8. 性能与限制", content: "性能指标、已知限制、注意事项" },
  { title: "9. 版本更新记录", content: "版本历史、主要更新内容" },
  { title: "10. 版权与声明", content: "版权声明、法律责任说明" },
];

export default function RulesPage() {
  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      <PageHeader
        title="申请规范"
        description="知识产权申请材料的格式要求与规范说明"
      />

      <Tabs defaultValue="copyright" className="space-y-6">
        <TabsList>
          <TabsTrigger value="copyright" className="gap-2" data-testid="tab-copyright-rules">
            <FileCode className="h-4 w-4" />
            软著申请
          </TabsTrigger>
          <TabsTrigger value="patent" className="gap-2" data-testid="tab-patent-rules">
            <Lightbulb className="h-4 w-4" />
            专利申请
          </TabsTrigger>
          <TabsTrigger value="trademark" className="gap-2" data-testid="tab-trademark-rules">
            <Stamp className="h-4 w-4" />
            商标申请
          </TabsTrigger>
        </TabsList>

        {/* ====== 软著申请规则 ====== */}
        <TabsContent value="copyright" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>源代码鉴别材料规范</CardTitle>
              <CardDescription>按照国家版权局要求，源代码材料需满足以下格式要求</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={copyrightCodeRules} />
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

          <Card>
            <CardHeader>
              <CardTitle>操作说明书规范</CardTitle>
              <CardDescription>说明书需完整描述软件的功能和使用方法</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={copyrightManualRules} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>说明书章节建议</CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="w-full">
                {manualChapters.map((item, index) => (
                  <AccordionItem key={index} value={`item-${index}`}>
                    <AccordionTrigger className="text-sm">{item.title}</AccordionTrigger>
                    <AccordionContent className="text-sm text-muted-foreground">{item.content}</AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>证明材料清单</CardTitle>
              <CardDescription>根据申请类型和开发方式，系统将自动提示所需证明材料</CardDescription>
            </CardHeader>
            <CardContent>
              <ProofRuleList rules={copyrightProofRules} />
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

        {/* ====== 专利申请规则 ====== */}
        <TabsContent value="patent" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>专利基本信息规范</CardTitle>
              <CardDescription>申请书中的基本信息需满足以下要求</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={patentInfoRules} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>权利要求书规范</CardTitle>
              <CardDescription>权利要求书用于限定专利保护范围</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={patentClaimsRules} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                权利要求撰写要点
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground space-y-2">
                <p>• 独立权利要求应完整描述技术方案的必要技术特征</p>
                <p>• 从属权利要求引用在前的权利要求号，并附加技术特征</p>
                <p>• 避免使用功能性限定，尽量用结构性语言描述</p>
                <p>• 保护范围从宽到窄依次排列</p>
                <p>• 每项权利要求用一个编号，独立成段</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>说明书规范</CardTitle>
              <CardDescription>说明书需按以下结构完整撰写</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={patentDescriptionRules} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                不同专利类型的差异
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="w-full">
                <AccordionItem value="invention">
                  <AccordionTrigger className="text-sm">发明专利</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground space-y-1">
                    <p>• 保护期限：20年（自申请日起）</p>
                    <p>• 审查方式：实质审查（初审 + 实审）</p>
                    <p>• 适用对象：产品、方法或其改进的新技术方案</p>
                    <p>• 附图要求：一般需要附图，但化学/生物领域可不提供</p>
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="utility">
                  <AccordionTrigger className="text-sm">实用新型</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground space-y-1">
                    <p>• 保护期限：10年（自申请日起）</p>
                    <p>• 审查方式：初步审查（无实质审查）</p>
                    <p>• 适用对象：产品形状、构造或其结合的新技术方案</p>
                    <p>• 附图要求：必须有附图</p>
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="design">
                  <AccordionTrigger className="text-sm">外观设计</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground space-y-1">
                    <p>• 保护期限：15年（自申请日起）</p>
                    <p>• 审查方式：初步审查</p>
                    <p>• 适用对象：产品外观的形状、图案、色彩设计</p>
                    <p>• 附图要求：必须提供六面视图或立体图</p>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>证明材料清单</CardTitle>
              <CardDescription>专利申请所需的证明材料</CardDescription>
            </CardHeader>
            <CardContent>
              <ProofRuleList rules={patentProofRules} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ====== 商标申请规则 ====== */}
        <TabsContent value="trademark" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>商标基本信息规范</CardTitle>
              <CardDescription>商标申请书中的基本信息要求</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={trademarkInfoRules} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>商标图样规范</CardTitle>
              <CardDescription>提交的商标图样需满足以下要求</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={trademarkImageRules} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>商品与服务分类规范</CardTitle>
              <CardDescription>按照尼斯分类体系选择商品/服务类别</CardDescription>
            </CardHeader>
            <CardContent>
              <RuleGrid rules={trademarkClassRules} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                常用尼斯分类（IT/互联网相关）
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="w-full">
                <AccordionItem value="class9">
                  <AccordionTrigger className="text-sm">第 9 类 — 科学仪器</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground">
                    计算机软件、电子设备、通信设备、数据处理装置、可下载的应用程序等
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="class35">
                  <AccordionTrigger className="text-sm">第 35 类 — 广告销售</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground">
                    通过网站提供商业信息、在线广告、电子商务平台服务、商业数据分析等
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="class38">
                  <AccordionTrigger className="text-sm">第 38 类 — 通讯服务</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground">
                    电信通讯服务、互联网接入、在线论坛、即时通讯、视频会议等
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="class41">
                  <AccordionTrigger className="text-sm">第 41 类 — 教育娱乐</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground">
                    在线教育、电子出版、游戏服务、虚拟现实娱乐等
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="class42">
                  <AccordionTrigger className="text-sm">第 42 类 — 科技服务</AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground">
                    软件开发、技术咨询、云计算、SaaS 服务、网站设计、数据安全等
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                商标注册注意事项
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground space-y-2">
                <p>• 商标查询：建议提交前先进行近似商标检索</p>
                <p>• 显著性：商标应具有识别商品/服务来源的显著特征</p>
                <p>• 禁用标志：不得使用国旗、国徽、红十字等禁用标志</p>
                <p>• 通用名称：行业通用名称不能注册为商标</p>
                <p>• 审查周期：一般 9-12 个月，含初审公告期 3 个月</p>
                <p>• 有效期限：注册商标有效期 10 年，期满可续展</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>证明材料清单</CardTitle>
              <CardDescription>商标申请所需的证明材料</CardDescription>
            </CardHeader>
            <CardContent>
              <ProofRuleList rules={trademarkProofRules} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
