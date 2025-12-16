import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, boolean, jsonb, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// 用户表
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

// 主体类型枚举
export const subjectTypes = ["individual", "enterprise", "institution"] as const;
export type SubjectType = typeof subjectTypes[number];

// 开发方式枚举
export const developmentMethods = ["independent", "cooperative", "commissioned", "derivative"] as const;
export type DevelopmentMethod = typeof developmentMethods[number];

// 发表状态枚举
export const publicationStatuses = ["unpublished", "published"] as const;
export type PublicationStatus = typeof publicationStatuses[number];

// 项目状态枚举
export const projectStatuses = ["draft", "in_progress", "completed", "exported"] as const;
export type ProjectStatus = typeof projectStatuses[number];

// 模板类型枚举
export const templateTypes = ["web", "mobile", "algorithm", "script", "desktop"] as const;
export type TemplateType = typeof templateTypes[number];

// 项目表
export const projects = pgTable("projects", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
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

// 软件信息表
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

// 代码包表
export const codeBundles = pgTable("code_bundles", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  fileName: text("file_name").notNull(),
  fileSize: integer("file_size").notNull(),
  totalLines: integer("total_lines"),
  extractedPages: integer("extracted_pages"),
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

// 文档包表
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

// 证明材料表
export const proofAssets = pgTable("proof_assets", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").notNull(),
  type: text("type").notNull(), // identity, contract, taskbook, license, inheritance
  fileName: text("file_name").notNull(),
  fileSize: integer("file_size").notNull(),
  uploadedAt: timestamp("uploaded_at").defaultNow(),
});

export const insertProofAssetSchema = createInsertSchema(proofAssets).omit({
  id: true,
  uploadedAt: true,
});

export type InsertProofAsset = z.infer<typeof insertProofAssetSchema>;
export type ProofAsset = typeof proofAssets.$inferSelect;

// 合规检查结果表
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

// 合规检查结果项类型
export interface ComplianceResult {
  ruleId: string;
  ruleName: string;
  category: "code" | "manual" | "proof" | "info";
  status: "passed" | "warning" | "failed" | "pending";
  message: string;
}

// 导出包表
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

// 向导步骤定义
export const wizardSteps = [
  { id: 1, name: "创建项目", description: "选择主体类型与开发方式" },
  { id: 2, name: "软件信息", description: "填写软件基本信息" },
  { id: 3, name: "代码材料", description: "上传并处理源代码" },
  { id: 4, name: "文档材料", description: "编写操作说明书" },
  { id: 5, name: "导出交付", description: "合规校验与打包导出" },
] as const;

// 模板类型中文映射
export const templateTypeLabels: Record<TemplateType, string> = {
  web: "Web/平台型",
  mobile: "移动App型",
  algorithm: "算法/SDK/库型",
  script: "脚本/工具型",
  desktop: "桌面客户端型",
};

// 主体类型中文映射
export const subjectTypeLabels: Record<SubjectType, string> = {
  individual: "个人",
  enterprise: "企业",
  institution: "高校/研究所/机构",
};

// 开发方式中文映射
export const developmentMethodLabels: Record<DevelopmentMethod, string> = {
  independent: "独立开发",
  cooperative: "合作开发",
  commissioned: "委托开发",
  derivative: "二次开发/改编",
};

// 发表状态中文映射
export const publicationStatusLabels: Record<PublicationStatus, string> = {
  unpublished: "未发表",
  published: "已发表",
};

// 项目状态中文映射
export const projectStatusLabels: Record<ProjectStatus, string> = {
  draft: "草稿",
  in_progress: "进行中",
  completed: "已完成",
  exported: "已导出",
};

// 证明材料类型
export const proofAssetTypes = [
  { id: "identity", name: "身份证明", description: "自然人/法人身份证明", required: true },
  { id: "contract", name: "合同/任务书", description: "开发合同或任务书", required: false },
  { id: "taskbook", name: "立项书", description: "项目立项或任务书", required: false },
  { id: "license", name: "许可证明", description: "二次开发许可证明", required: false },
  { id: "inheritance", name: "继承/受让证明", description: "权利继承或受让证明", required: false },
] as const;

// 合规规则定义
export const complianceRules = {
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
} as const;
