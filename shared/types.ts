// === 纯类型定义文件（前端安全导入）===

// === 用户角色 ===
export const userRoles = ["admin", "user"] as const;
export type UserRole = typeof userRoles[number];

export interface User {
  id: string;
  username: string;
  // 注意：密码绝不应出现在客户端类型中（已移除 password 字段，避免后端密钥形状泄漏到前端）
  displayName: string | null;
  name?: string;
  avatar?: string;
  email?: string;
  role: string;
  createdAt: Date;
}

export interface InsertUser {
  username: string;
  password: string;
  displayName?: string;
}

// === 项目类型枚举 ===
export const projectTypes = ["copyright", "patent", "trademark"] as const;
export type ProjectType = typeof projectTypes[number];

// === 软著相关枚举 ===
export const subjectTypes = ["individual", "enterprise", "institution"] as const;
export type SubjectType = typeof subjectTypes[number];

export const developmentMethods = ["independent", "cooperative", "commissioned", "derivative"] as const;
export type DevelopmentMethod = typeof developmentMethods[number];

export const publicationStatuses = ["unpublished", "published"] as const;
export type PublicationStatus = typeof publicationStatuses[number];

// === 专利相关枚举 ===
export const patentTypes = ["invention", "utility_model", "design"] as const;
export type PatentType = typeof patentTypes[number];

export const patentStatuses = ["drafting", "reviewing", "filed", "accepted"] as const;
export type PatentStatus = typeof patentStatuses[number];

// === 商标相关枚举 ===
export const trademarkTypes = ["word", "device", "composite", "3d", "sound", "color"] as const;
export type TrademarkType = typeof trademarkTypes[number];

// === 通用枚举 ===
export const projectStatuses = [
  "draft",
  "in_progress",
  "reviewing",
  "pending_submit",
  "submitted",
  "accepted",
  "approved",
  "rejected",
  "withdrawn",
  "completed",
  "exported",
] as const;
export type ProjectStatus = typeof projectStatuses[number];

export const templateTypes = ["web", "mobile", "algorithm", "script", "desktop"] as const;
export type TemplateType = typeof templateTypes[number];

// === 项目类型 ===
//
// 字段命名与后端 SQLModel 响应保持一致（snake_case）。
// 后端 ``Project`` 模型字段：project_type / subject_type / flow_status /
// current_step / created_at / updated_at 等，均为 snake_case。
export interface Project {
  id: string;
  project_type: ProjectType;
  /** 兼容历史：少量旧调用仍使用 ``type``，保留可选别名 */
  type?: ProjectType;
  name: string;
  version: string;
  description?: string;
  subject_type: SubjectType;
  subject_name?: string;
  development_method?: DevelopmentMethod;
  publication_status?: PublicationStatus;
  status: ProjectStatus;
  current_step: number;
  flow_status?: string;
  owner_id?: string;
  organization_id?: string;
  created_at: string | Date | null;
  updated_at: string | Date | null;
}

export interface InsertProject {
  project_type: ProjectType;
  name: string;
  version?: string;
  subject_type?: SubjectType;
  subject_name?: string;
  development_method?: DevelopmentMethod;
  publication_status?: PublicationStatus;
  status?: ProjectStatus;
  current_step?: number;
}

// === 软件信息（软著专用）===
export interface SoftwareInfo {
  id: string;
  projectId: string;
  fullName: string;
  shortName: string | null;
  versionNumber: string;
  developmentLanguage: string;
  developmentEnvironment: string | null;
  runtimeEnvironment: string | null;
  codeLineCount: number | null;
  functionalDescription: string | null;
  technicalFeatures: string | null;
  targetDomain: string | null;
  completionDate: string | null;
}

export interface InsertSoftwareInfo {
  projectId: string;
  fullName: string;
  shortName?: string;
  versionNumber: string;
  developmentLanguage: string;
  developmentEnvironment?: string;
  runtimeEnvironment?: string;
  codeLineCount?: number;
  functionalDescription?: string;
  technicalFeatures?: string;
  targetDomain?: string;
  completionDate?: string;
}

// === 专利信息 ===
export interface PatentInfo {
  id: string;
  projectId: string;
  patentType: PatentType;
  title: string;
  abstract: string | null;
  applicantName: string;
  applicantAddress: string | null;
  inventorNames: string[] | null;
  agencyName: string | null;
  agentName: string | null;
  claimsText: string | null;
  descriptionText: string | null;
  drawingsDescription: string | null;
  technicalField: string | null;
  backgroundArt: string | null;
  technicalProblem: string | null;
  technicalSolution: string | null;
  beneficialEffects: string | null;
  priorityDate: string | null;
  filingDate: string | null;
}

export interface InsertPatentInfo {
  projectId: string;
  patentType: PatentType;
  title: string;
  abstract?: string;
  applicantName: string;
  applicantAddress?: string;
  inventorNames?: string[];
  agencyName?: string;
  agentName?: string;
  claimsText?: string;
  descriptionText?: string;
  drawingsDescription?: string;
  technicalField?: string;
  backgroundArt?: string;
  technicalProblem?: string;
  technicalSolution?: string;
  beneficialEffects?: string;
  priorityDate?: string;
  filingDate?: string;
}

// === 商标信息 ===
export interface NiceClassSelection {
  classNumber: number;
  className: string;
  selectedItems: string[];
}

export interface TrademarkInfo {
  id: string;
  projectId: string;
  trademarkType: TrademarkType;
  trademarkName: string;
  applicantName: string;
  applicantAddress: string | null;
  applicantType: "individual" | "enterprise" | "institution" | null;
  contactPerson: string | null;
  contactPhone: string | null;
  contactEmail: string | null;
  niceClasses: NiceClassSelection[] | null;
  colorClaim: string | null;
  designDescription: string | null;
  imageObjectPath: string | null;
  filingDate: string | null;
}

export interface InsertTrademarkInfo {
  projectId: string;
  trademarkType: TrademarkType;
  trademarkName: string;
  applicantName: string;
  applicantAddress?: string;
  applicantType?: "individual" | "enterprise" | "institution";
  contactPerson?: string;
  contactPhone?: string;
  contactEmail?: string;
  niceClasses?: NiceClassSelection[];
  colorClaim?: string;
  designDescription?: string;
  imageObjectPath?: string;
  filingDate?: string;
}

// === 代码页面类型 ===
export interface CodePageData {
  pageNumber: number;
  content: string;
  lineStart: number;
  lineEnd: number;
  section: 'first' | 'last';
}

// === 代码包（软著专用）===
export interface CodeBundle {
  id: string;
  projectId: string;
  fileName: string;
  fileSize: number;
  totalLines: number | null;
  extractedPages: number | null;
  extractedContent: string | null;
  pagesData: CodePageData[] | null;
  hasEnoughCode: boolean | null;
  language: string | null;
  uploadedAt: Date | null;
  processedAt: Date | null;
  status: string;
}

export interface InsertCodeBundle {
  projectId: string;
  fileName: string;
  fileSize: number;
  totalLines?: number;
  extractedPages?: number;
  extractedContent?: string;
  pagesData?: CodePageData[];
  hasEnoughCode?: boolean;
  language?: string;
  status?: string;
}

// === 文档包（软著操作说明书）===
export interface ManualBundle {
  id: string;
  projectId: string;
  templateType: TemplateType;
  content: string | null;
  wordCount: number | null;
  pageCount: number | null;
  screenshotCount: number | null;
  createdAt: Date | null;
  updatedAt: Date | null;
}

export interface InsertManualBundle {
  projectId: string;
  templateType: TemplateType;
  content?: string;
  wordCount?: number;
  pageCount?: number;
  screenshotCount?: number;
}

// === 证明材料（通用）===
export interface ProofAsset {
  id: string;
  projectId: string;
  type: string;
  fileName: string;
  fileSize: number;
  objectPath: string | null;
  uploadedAt: Date | null;
}

export interface InsertProofAsset {
  projectId: string;
  type: string;
  fileName: string;
  fileSize: number;
  objectPath?: string;
}

// === 合规检查结果（通用）===
export interface ComplianceResult {
  ruleId: string;
  ruleName: string;
  category: string;
  status: "passed" | "warning" | "failed" | "pending";
  message: string;
}

export interface ComplianceRun {
  id: string;
  projectId: string;
  results: ComplianceResult[] | null;
  overallStatus: string;
  checkedAt: Date | null;
}

export interface InsertComplianceRun {
  projectId: string;
  results?: ComplianceResult[];
  overallStatus?: string;
}

// === 导出包（通用）===
export interface ExportPackage {
  id: string;
  projectId: string;
  version: string;
  fileName: string;
  fileSize: number | null;
  createdAt: Date | null;
}

export interface InsertExportPackage {
  projectId: string;
  version: string;
  fileName: string;
  fileSize?: number;
}

// === 向导步骤定义（按项目类型）===
export const copyrightWizardSteps = [
  { id: 1, name: "创建项目", description: "选择主体类型与开发方式" },
  { id: 2, name: "软件信息", description: "填写软件基本信息" },
  { id: 3, name: "代码材料", description: "上传并处理源代码" },
  { id: 4, name: "文档材料", description: "编写操作说明书" },
  { id: 5, name: "导出交付", description: "合规校验与打包导出" },
] as const;

export const patentWizardSteps = [
  { id: 1, name: "创建项目", description: "选择专利类型与基本信息" },
  { id: 2, name: "专利信息", description: "填写发明名称与摘要" },
  { id: 3, name: "权利要求", description: "编写权利要求书" },
  { id: 4, name: "说明书", description: "编写说明书与附图" },
  { id: 5, name: "导出交付", description: "合规校验与打包导出" },
] as const;

export const trademarkWizardSteps = [
  { id: 1, name: "创建项目", description: "选择商标类型与基本信息" },
  { id: 2, name: "商标信息", description: "填写商标名称与图样" },
  { id: 3, name: "商品服务", description: "选择尼斯分类与商品服务" },
  { id: 4, name: "导出交付", description: "合规校验与打包导出" },
] as const;

export function getWizardSteps(type: ProjectType) {
  switch (type) {
    case "copyright": return copyrightWizardSteps;
    case "patent": return patentWizardSteps;
    case "trademark": return trademarkWizardSteps;
  }
}

export function getMaxSteps(type: ProjectType): number {
  return getWizardSteps(type).length;
}

// === 中文标签映射 ===
export const projectTypeLabels: Record<ProjectType, string> = {
  copyright: "软著申请",
  patent: "专利申请",
  trademark: "商标申请",
};

export const projectTypeDescriptions: Record<ProjectType, string> = {
  copyright: "计算机软件著作权登记",
  patent: "发明/实用新型/外观设计专利申请",
  trademark: "商标注册申请",
};

export const templateTypeLabels: Record<TemplateType, string> = {
  web: "Web/平台型",
  mobile: "移动App型",
  algorithm: "算法/SDK/库型",
  script: "脚本/工具型",
  desktop: "桌面客户端型",
};

export const subjectTypeLabels: Record<SubjectType, string> = {
  individual: "个人",
  enterprise: "企业",
  institution: "高校/研究所/机构",
};

export const developmentMethodLabels: Record<DevelopmentMethod, string> = {
  independent: "独立开发",
  cooperative: "合作开发",
  commissioned: "委托开发",
  derivative: "二次开发/改编",
};

export const publicationStatusLabels: Record<PublicationStatus, string> = {
  unpublished: "未发表",
  published: "已发表",
};

export const patentTypeLabels: Record<PatentType, string> = {
  invention: "发明专利",
  utility_model: "实用新型",
  design: "外观设计",
};

export const trademarkTypeLabels: Record<TrademarkType, string> = {
  word: "文字商标",
  device: "图形商标",
  composite: "组合商标",
  "3d": "三维商标",
  sound: "声音商标",
  color: "颜色商标",
};

export const projectStatusLabels: Record<ProjectStatus, string> = {
  draft: "草稿",
  in_progress: "进行中",
  reviewing: "审核中",
  pending_submit: "待提交",
  submitted: "已提交",
  accepted: "已受理",
  approved: "已通过",
  rejected: "已驳回",
  withdrawn: "已撤回",
  completed: "已完成",
  exported: "已导出",
};

// === 证明材料类型（按项目类型）===
export const copyrightProofAssetTypes = [
  { id: "identity", name: "身份证明", description: "自然人/法人身份证明", required: true },
  { id: "contract", name: "合同/任务书", description: "开发合同或任务书", required: false },
  { id: "taskbook", name: "立项书", description: "项目立项或任务书", required: false },
  { id: "license", name: "许可证明", description: "二次开发许可证明", required: false },
  { id: "inheritance", name: "继承/受让证明", description: "权利继承或受让证明", required: false },
] as const;

export const patentProofAssetTypes = [
  { id: "identity", name: "身份证明", description: "申请人身份证明", required: true },
  { id: "power_of_attorney", name: "委托书", description: "专利代理委托书", required: false },
  { id: "priority_doc", name: "优先权证明", description: "优先权文件", required: false },
  { id: "drawings", name: "附图", description: "说明书附图", required: false },
  { id: "abstract_drawing", name: "摘要附图", description: "摘要附图", required: false },
  { id: "sequence_listing", name: "序列表", description: "生物序列表", required: false },
] as const;

export const trademarkProofAssetTypes = [
  { id: "identity", name: "身份证明", description: "申请人身份证明", required: true },
  { id: "trademark_image", name: "商标图样", description: "清晰的商标图样", required: true },
  { id: "power_of_attorney", name: "委托书", description: "商标代理委托书", required: false },
  { id: "priority_doc", name: "优先权证明", description: "优先权证明文件", required: false },
  { id: "usage_evidence", name: "使用证据", description: "商标使用证据", required: false },
] as const;

export function getProofAssetTypes(type: ProjectType) {
  switch (type) {
    case "copyright": return copyrightProofAssetTypes;
    case "patent": return patentProofAssetTypes;
    case "trademark": return trademarkProofAssetTypes;
  }
}

// === 合规规则定义 ===
export const complianceRules = {
  copyright: {
    code: {
      pages: 60,
      segments: ["first:30", "last:30"],
      minLinesPerPage: 50,
      pageHeader: "${softwareFullName} ${version}",
    },
    manual: {
      minPages: 15,
      extractRule: "<60:all, >=60:first30+last30",
      minLinesPerPage: 30,
    },
    proofs: ["identity", "contractOrTaskbook?", "licenseForDerivative?", "inheritOrAssignment?"],
  },
  patent: {
    claims: {
      minClaims: 1,
      requireIndependentClaim: true,
    },
    description: {
      requiredSections: ["technicalField", "backgroundArt", "technicalProblem", "technicalSolution", "beneficialEffects"],
    },
    proofs: ["identity", "powerOfAttorney?", "priorityDoc?"],
  },
  trademark: {
    info: {
      requireImage: true,
      imageMinSize: 500,
      imageMaxSize: 2000,
    },
    classification: {
      minClasses: 1,
      minItemsPerClass: 1,
    },
    proofs: ["identity", "trademarkImage", "powerOfAttorney?"],
  },
} as const;

// === 尼斯分类（常用类别）===
export const niceClassifications = [
  { classNumber: 9, name: "科学仪器", description: "计算机软件、电子设备、通信设备等" },
  { classNumber: 35, name: "广告销售", description: "广告、商业管理、市场营销等" },
  { classNumber: 38, name: "通讯服务", description: "电信、通信服务等" },
  { classNumber: 41, name: "教育娱乐", description: "教育、培训、娱乐、体育等" },
  { classNumber: 42, name: "科技服务", description: "软件开发、技术咨询、云计算等" },
  { classNumber: 1, name: "化学原料", description: "化学制品、工业化学品等" },
  { classNumber: 2, name: "颜料油漆", description: "颜料、涂料、油墨等" },
  { classNumber: 3, name: "日化用品", description: "洗涤剂、化妆品等" },
  { classNumber: 5, name: "医药卫生", description: "药品、医疗用品等" },
  { classNumber: 7, name: "机械设备", description: "机器、机床、发动机等" },
  { classNumber: 10, name: "医疗器械", description: "医疗器械、假肢等" },
  { classNumber: 11, name: "灯具空调", description: "照明、加热、冷却设备等" },
  { classNumber: 12, name: "运输工具", description: "车辆、船舶、飞行器等" },
  { classNumber: 14, name: "珠宝钟表", description: "贵金属、珠宝、钟表等" },
  { classNumber: 16, name: "办公用品", description: "纸张、印刷品、文具等" },
  { classNumber: 18, name: "皮革箱包", description: "皮革、箱包、伞等" },
  { classNumber: 20, name: "家具用品", description: "家具、镜子、相框等" },
  { classNumber: 21, name: "厨房洁具", description: "厨房用具、玻璃器皿等" },
  { classNumber: 24, name: "纺织品", description: "织物、床单、桌布等" },
  { classNumber: 25, name: "服装鞋帽", description: "服装、鞋、帽等" },
  { classNumber: 28, name: "游戏器具", description: "游戏器具、体育用品等" },
  { classNumber: 29, name: "食品鱼肉", description: "肉、鱼、果蔬制品等" },
  { classNumber: 30, name: "方便食品", description: "咖啡、茶、糕点等" },
  { classNumber: 31, name: "饲料种籽", description: "谷物、鲜果、花卉等" },
  { classNumber: 32, name: "啤酒饮料", description: "啤酒、矿泉水、果汁等" },
  { classNumber: 33, name: "酒", description: "含酒精饮料（啤酒除外）" },
  { classNumber: 36, name: "金融物管", description: "保险、金融、不动产管理等" },
  { classNumber: 37, name: "建筑修理", description: "建筑施工、安装维修等" },
  { classNumber: 39, name: "运输贮藏", description: "运输、旅行安排等" },
  { classNumber: 40, name: "材料加工", description: "材料处理、加工等" },
  { classNumber: 43, name: "餐饮住宿", description: "餐饮服务、住宿服务等" },
  { classNumber: 44, name: "医疗园艺", description: "医疗、美容、园艺等" },
  { classNumber: 45, name: "社会服务", description: "法律、安保、社交等" },
] as const;
