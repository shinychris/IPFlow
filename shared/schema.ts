import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, boolean, jsonb, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

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
export const trademarkTypes = ["text", "graphic", "combined", "3d", "sound", "color"] as const;
export type TrademarkType = typeof trademarkTypes[number];

// === 通用枚举 ===
export const projectStatuses = ["draft", "in_progress", "completed", "exported"] as const;
export type ProjectStatus = typeof projectStatuses[number];

export const templateTypes = ["web", "mobile", "algorithm", "script", "desktop"] as const;
export type TemplateType = typeof templateTypes[number];

// === 项目表（增加 type 字段） ===
export const projects = pgTable("projects", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  type: text("type").notNull().default("copyright").$type<ProjectType>(),
  name: text("name").notNull(),
  version: text("version").notNull().default("V1.0"),
  subjectType: text("subject_type").notNull().$type<SubjectType>(),
  developmentMethod: text("development_method").notNull().$type<DevelopmentMethod>(),
  publicationStatus: text("publication_status").notNull().$type<PublicationStatus>(),
  status: text("status").notNull().default("draft").$type<ProjectStatus>(),
  currentStep: integer("current_step").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const insertProjectSchema = createInsertSchema(projects).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertProject = z.infer<typeof insertProjectSchema>;
export type Project = typeof projects.$inferSelect;

// === 软件信息表（软著专用） ===
export const softwareInfo = pgTable("software_info", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  fullName: text("full_name").notNull(),
  shortName: text("short_name"),
  versionNumber: text("version_number").notNull(),
  developmentLanguage: text("development_language").notNull(),
  developmentEnvironment: text("development_environment"),
  runtimeEnvironment: text("runtime_environment"),
  codeLineCount: integer("code_line_count"),
  functionalDescription: text("functional_description"),
  technicalFeatures: text("technical_features"),
  targetDomain: text("target_domain"),
  completionDate: text("completion_date"),
});

export const insertSoftwareInfoSchema = createInsertSchema(softwareInfo).omit({
  id: true,
});

export type InsertSoftwareInfo = z.infer<typeof insertSoftwareInfoSchema>;
export type SoftwareInfo = typeof softwareInfo.$inferSelect;

// === 专利信息表 ===
export const patentInfo = pgTable("patent_info", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  patentType: text("patent_type").notNull().$type<PatentType>(),
  title: text("title").notNull(),
  abstract: text("abstract"),
  applicantName: text("applicant_name").notNull(),
  applicantAddress: text("applicant_address"),
  inventorNames: text("inventor_names").array(),
  agencyName: text("agency_name"),
  agentName: text("agent_name"),
  claimsText: text("claims_text"),
  descriptionText: text("description_text"),
  drawingsDescription: text("drawings_description"),
  technicalField: text("technical_field"),
  backgroundArt: text("background_art"),
  technicalProblem: text("technical_problem"),
  technicalSolution: text("technical_solution"),
  beneficialEffects: text("beneficial_effects"),
  priorityDate: text("priority_date"),
  filingDate: text("filing_date"),
});

export const insertPatentInfoSchema = createInsertSchema(patentInfo).omit({
  id: true,
});

export type InsertPatentInfo = z.infer<typeof insertPatentInfoSchema>;
export type PatentInfo = typeof patentInfo.$inferSelect;

// === 商标信息表 ===
export const trademarkInfo = pgTable("trademark_info", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  trademarkType: text("trademark_type").notNull().$type<TrademarkType>(),
  trademarkName: text("trademark_name").notNull(),
  applicantName: text("applicant_name").notNull(),
  applicantAddress: text("applicant_address"),
  applicantType: text("applicant_type").$type<"individual" | "enterprise" | "institution">(),
  contactPerson: text("contact_person"),
  contactPhone: text("contact_phone"),
  contactEmail: text("contact_email"),
  niceClasses: jsonb("nice_classes").$type<NiceClassSelection[]>(),
  colorClaim: text("color_claim"),
  designDescription: text("design_description"),
  imageObjectPath: text("image_object_path"),
  filingDate: text("filing_date"),
});

export const insertTrademarkInfoSchema = createInsertSchema(trademarkInfo).omit({
  id: true,
});

export type InsertTrademarkInfo = z.infer<typeof insertTrademarkInfoSchema>;
export type TrademarkInfo = typeof trademarkInfo.$inferSelect;

export interface NiceClassSelection {
  classNumber: number;
  className: string;
  selectedItems: string[];
}

// === 代码页面类型 ===
export interface CodePageData {
  pageNumber: number;
  content: string;
  lineStart: number;
  lineEnd: number;
  section: 'first' | 'last';
}

// === 代码包表（软著专用） ===
export const codeBundles = pgTable("code_bundles", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  fileName: text("file_name").notNull(),
  fileSize: integer("file_size").notNull(),
  totalLines: integer("total_lines"),
  extractedPages: integer("extracted_pages"),
  extractedContent: text("extracted_content"),
  pagesData: jsonb("pages_data").$type<CodePageData[]>(),
  hasEnoughCode: boolean("has_enough_code").default(true),
  language: text("language"),
  uploadedAt: timestamp("uploaded_at").defaultNow(),
  processedAt: timestamp("processed_at"),
  status: text("status").notNull().default("pending"),
});

export const insertCodeBundleSchema = createInsertSchema(codeBundles).omit({
  id: true,
  uploadedAt: true,
  processedAt: true,
});

export type InsertCodeBundle = z.infer<typeof insertCodeBundleSchema>;
export type CodeBundle = typeof codeBundles.$inferSelect;

// === 文档包表（软著操作说明书） ===
export const manualBundles = pgTable("manual_bundles", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  templateType: text("template_type").notNull().$type<TemplateType>(),
  content: text("content"),
  wordCount: integer("word_count"),
  pageCount: integer("page_count"),
  screenshotCount: integer("screenshot_count"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const insertManualBundleSchema = createInsertSchema(manualBundles).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertManualBundle = z.infer<typeof insertManualBundleSchema>;
export type ManualBundle = typeof manualBundles.$inferSelect;

// === 证明材料表（通用，三种类型共用） ===
export const proofAssets = pgTable("proof_assets", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  type: text("type").notNull(),
  fileName: text("file_name").notNull(),
  fileSize: integer("file_size").notNull(),
  objectPath: text("object_path"),
  uploadedAt: timestamp("uploaded_at").defaultNow(),
});

export const insertProofAssetSchema = createInsertSchema(proofAssets).omit({
  id: true,
  uploadedAt: true,
});

export type InsertProofAsset = z.infer<typeof insertProofAssetSchema>;
export type ProofAsset = typeof proofAssets.$inferSelect;

// === 合规检查结果表（通用） ===
export const complianceRuns = pgTable("compliance_runs", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  results: jsonb("results").$type<ComplianceResult[]>(),
  overallStatus: text("overall_status").notNull().default("pending"),
  checkedAt: timestamp("checked_at").defaultNow(),
});

export const insertComplianceRunSchema = createInsertSchema(complianceRuns).omit({
  id: true,
  checkedAt: true,
});

export type InsertComplianceRun = z.infer<typeof insertComplianceRunSchema>;
export type ComplianceRun = typeof complianceRuns.$inferSelect;

export interface ComplianceResult {
  ruleId: string;
  ruleName: string;
  category: string;
  status: "passed" | "warning" | "failed" | "pending";
  message: string;
}

// === 导出包表（通用） ===
export const exportPackages = pgTable("export_packages", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  version: text("version").notNull(),
  fileName: text("file_name").notNull(),
  fileSize: integer("file_size"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertExportPackageSchema = createInsertSchema(exportPackages).omit({
  id: true,
  createdAt: true,
});

export type InsertExportPackage = z.infer<typeof insertExportPackageSchema>;
export type ExportPackage = typeof exportPackages.$inferSelect;

// === 向导步骤定义（按项目类型） ===
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
  text: "文字商标",
  graphic: "图形商标",
  combined: "组合商标",
  "3d": "三维商标",
  sound: "声音商标",
  color: "颜色商标",
};

export const projectStatusLabels: Record<ProjectStatus, string> = {
  draft: "草稿",
  in_progress: "进行中",
  completed: "已完成",
  exported: "已导出",
};

// === 证明材料类型（按项目类型） ===
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

// === 尼斯分类（常用类别） ===
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
