/**
 * IPFlow 类型定义
 * 
 * 与后端 Pydantic 模型保持同步
 */

// ============================================================================
// 枚举类型
// ============================================================================

export enum ProjectType {
  COPYRIGHT = "copyright",
  PATENT = "patent",
  TRADEMARK = "trademark",
}

export enum ProjectStatus {
  DRAFT = "draft",
  IN_PROGRESS = "in_progress",
  REVIEWING = "reviewing",
  PENDING_SUBMIT = "pending_submit",
  SUBMITTED = "submitted",
  ACCEPTED = "accepted",
  APPROVED = "approved",
  REJECTED = "rejected",
  WITHDRAWN = "withdrawn",
}

export enum SubjectType {
  INDIVIDUAL = "individual",
  ENTERPRISE = "enterprise",
  INSTITUTION = "institution",
  AGENCY = "agency",
}

export enum ManualTemplateType {
  WEB = "web",
  MOBILE = "mobile",
  ALGORITHM = "algorithm",
  SCRIPT = "script",
  DESKTOP = "desktop",
}

export enum UserRole {
  SUPER_ADMIN = "super_admin",
  ADMIN = "admin",
  MANAGER = "manager",
  MEMBER = "member",
  VIEWER = "viewer",
}

export enum UserStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SUSPENDED = "suspended",
  PENDING = "pending",
}

// 专利类型
export enum PatentType {
  INVENTION = "invention",
  UTILITY_MODEL = "utility_model",
  DESIGN = "design",
}

// 商标类型
export enum TrademarkType {
  WORD = "word",
  DEVICE = "device",
  COMPOSITE = "composite",
  THREE_D = "3d",
  SOUND = "sound",
  COLOR = "color",
}

// ============================================================================
// 基础模型
// ============================================================================

export interface User {
  id: string;
  email: string;
  username: string;
  display_name?: string;
  avatar_url?: string;
  phone?: string;
  role: UserRole;
  status: UserStatus;
  is_verified: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
  // 前端兼容字段 (camelCase)
  displayName?: string;
  avatar?: string;
  name?: string;
}

export interface Project {
  id: string;
  owner_id?: string;
  project_type?: ProjectType;
  type?: ProjectType;
  status?: ProjectStatus;
  current_step?: number;
  currentStep?: number;
  flow_status?: string;
  name: string;
  version: string;
  description?: string;
  subject_type?: SubjectType;
  subjectType?: SubjectType;
  subject_name?: string;
  subject_id_number?: string;
  development_method?: string;
  publication_status?: string;
  completion_date?: string;
  first_publication_date?: string;
  tags?: string[];
  meta_info?: Record<string, any>;
  completeness_score?: number;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// 软著相关模型
// ============================================================================

export interface CopyrightData {
  id: string;
  project_id: string;
  software_full_name: string;
  software_short_name?: string;
  version_number: string;
  development_language: string;
  development_environment?: string;
  runtime_environment?: string;
  code_line_count?: number;
  functional_description?: string;
  technical_features?: string;
  target_domain?: string;
  source?: "ai" | "human" | "mixed";
  revision?: number;
  is_confirmed?: boolean;
  last_edited_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CodeBundle {
  id: string;
  copyright_data_id: string;
  original_file_name: string;
  original_file_size: number;
  total_files: number;
  total_lines: number;
  processed_lines: number;
  pages_data: PageData[];
  language_stats: Record<string, number>;
  has_enough_code: boolean;
  warnings: string[];
  created_at: string;
}

export interface PageData {
  page_number: number;
  content: string;
  line_start: number;
  line_end: number;
  section: "front" | "back";
}

export interface CopyrightManual {
  id: string;
  copyright_data_id: string;
  template_type: string;
  title: string;
  content_html?: string;
  content_json?: Record<string, any>;
  word_count?: number;
  page_count?: number;
  screenshot_count: number;
  has_toc: boolean;
  has_chapters: boolean;
  source?: "ai" | "human" | "mixed";
  revision?: number;
  is_confirmed?: boolean;
  last_edited_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GenerationContext {
  project_id: string;
  project_type: string;
  base_profile: {
    name: string;
    version: string;
    description?: string;
    subject_name?: string;
  };
  optional_inputs: {
    code_repo?: unknown;
    extra_brief?: string;
    history_reuse?: { enabled: boolean; source_project_ids: string[] };
    org_knowledge?: { enabled: boolean; dataset_ids: string[] };
  };
  capability_flags: {
    can_use_repo: boolean;
    can_use_history: boolean;
    can_use_org_knowledge: boolean;
  };
  draft_exists: boolean;
}

export interface GenerationJob {
  id?: string;
  job_id?: string;
  project_id?: string;
  job_type?: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  progress: number;
  current_step?: string;
  error?: string | null;
  artifacts?: Record<string, unknown>;
  created_at?: string;
  finished_at?: string | null;
}

export interface ExportJob {
  id?: string;
  export_job_id?: string;
  project_id?: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  progress: number;
  current_step?: string;
  error?: string | null;
  download_url?: string | null;
  file_name?: string | null;
  expires_at?: string | null;
}

// ============================================================================
// 专利相关模型
// ============================================================================

export interface PatentInfo {
  id: string;
  project_id: string;
  patent_type: PatentType;
  title: string;
  abstract?: string;
  applicant_name: string;
  applicant_address?: string;
  inventor_names?: string[];
  agency_name?: string;
  agent_name?: string;
  claims_text?: string;
  description_text?: string;
  drawings_description?: string;
  technical_field?: string;
  background_art?: string;
  technical_problem?: string;
  technical_solution?: string;
  beneficial_effects?: string;
  priority_date?: string;
  filing_date?: string;
  created_at: string;
  updated_at: string;
}

export interface PatentProofAsset {
  id: string;
  project_id: string;
  type: string;
  file_name: string;
  file_size: number;
  object_path?: string;
  uploaded_at: string;
}

// ============================================================================
// 商标相关模型
// ============================================================================

export interface NiceClassSelection {
  class_number: number;
  class_name: string;
  selected_items: string[];
}

export interface TrademarkInfo {
  id: string;
  project_id: string;
  trademark_type: TrademarkType;
  trademark_name: string;
  applicant_name: string;
  applicant_address?: string;
  applicant_type?: "individual" | "enterprise" | "institution";
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  nice_classes?: NiceClassSelection[];
  color_claim?: string;
  design_description?: string;
  image_object_path?: string;
  filing_date?: string;
  created_at: string;
  updated_at: string;
}

export interface TrademarkProofAsset {
  id: string;
  project_id: string;
  type: string;
  file_name: string;
  file_size: number;
  object_path?: string;
  uploaded_at: string;
}

// ============================================================================
// 通用模型
// ============================================================================

export interface FileUpload {
  id: string;
  project_id?: string;
  original_name: string;
  file_size: number;
  mime_type: string;
  file_category: string;
  file_type?: string;
  processing_status: "pending" | "processing" | "completed" | "failed";
  processing_result?: Record<string, any>;
  created_at: string;
}

export interface ProofAsset {
  id: string;
  project_id: string;
  type: string;
  file_name: string;
  file_size: number;
  object_path?: string;
  uploaded_at: string;
}

// ============================================================================
// API 请求/响应类型
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  code: string;
  message: string;
  data?: T;
  meta?: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  username: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  display_name?: string;
}

export interface CreateProjectRequest {
  name: string;
  project_type: ProjectType;
  subject_type: SubjectType;
  version?: string;
  description?: string;
  development_method?: string;
  publication_status?: string;
  subject_name?: string;
  subject_id_number?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  status?: ProjectStatus;
  current_step?: number;
  version?: string;
  description?: string;
  subject_name?: string;
  subject_id_number?: string;
  completion_date?: string;
  first_publication_date?: string;
  tags?: string[];
  meta_info?: Record<string, any>;
}

// 软著信息请求
export interface SoftwareInfoRequest {
  software_full_name: string;
  software_short_name?: string;
  version_number: string;
  development_language: string;
  development_environment?: string;
  runtime_environment?: string;
  code_line_count?: number;
  functional_description?: string;
  technical_features?: string;
  target_domain?: string;
}

// 专利信息请求
export interface PatentInfoRequest {
  patent_type: PatentType;
  title: string;
  abstract?: string;
  applicant_name: string;
  applicant_address?: string;
  inventor_names?: string[];
  agency_name?: string;
  agent_name?: string;
  claims_text?: string;
  description_text?: string;
  drawings_description?: string;
  technical_field?: string;
  background_art?: string;
  technical_problem?: string;
  technical_solution?: string;
  beneficial_effects?: string;
  priority_date?: string;
  filing_date?: string;
}

// 商标信息请求
export interface TrademarkInfoRequest {
  trademark_type: TrademarkType;
  trademark_name: string;
  applicant_name: string;
  applicant_address?: string;
  applicant_type?: "individual" | "enterprise" | "institution";
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  nice_classes?: NiceClassSelection[];
  color_claim?: string;
  design_description?: string;
  filing_date?: string;
}

export interface CreateManualRequest {
  template_type: ManualTemplateType;
  title: string;
  content_html?: string;
  content_json?: Record<string, any>;
}

// ============================================================================
// 合规检查类型
// ============================================================================

export interface ComplianceResult {
  rule_id: string;
  rule_name: string;
  category: "info" | "code" | "manual" | "proof" | "claims" | "description" | "classification";
  status: "passed" | "warning" | "failed" | "skipped" | "pending";
  message: string;
  suggestion?: string;
}

export interface ComplianceReport {
  project_id: string;
  total_rules: number;
  passed: number;
  warnings: number;
  failed: number;
  overall_status: "passed" | "warning" | "failed";
  can_export: boolean;
  results: ComplianceResult[];
}

// ============================================================================
// 导出预览类型
// ============================================================================

export interface ExportPreview {
  // 软著导出预览
  software_info?: {
    has_data: boolean;
    software_name?: string;
  };
  code_bundle?: {
    has_data: boolean;
    total_pages: number;
    has_enough_code: boolean;
  };
  manual?: {
    has_data: boolean;
    page_count: number;
  };
  // 专利导出预览
  patent_info?: {
    has_data: boolean;
    title?: string;
  };
  claims?: {
    has_data: boolean;
  };
  description?: {
    has_data: boolean;
  };
  // 商标导出预览
  trademark_info?: {
    has_data: boolean;
    trademark_name?: string;
  };
  classification?: {
    has_data: boolean;
    class_count?: number;
  };
  // 通用
  files_in_package: string[];
}

// ============================================================================
// 尼斯分类类型
// ============================================================================

export interface NiceClassification {
  class_number: number;
  name: string;
  description: string;
}

// ============================================================================
// 标签映射类型
// ============================================================================

export interface ProjectTypeLabels {
  copyright: string;
  patent: string;
  trademark: string;
}

export interface PatentTypeLabels {
  invention: string;
  utility_model: string;
  design: string;
}

export interface TrademarkTypeLabels {
  word: string;
  device: string;
  composite: string;
  "3d": string;
  sound: string;
  color: string;
}

// ============================================================================
// 组织和成员类型
// ============================================================================

export interface Organization {
  id: string;
  name: string;
  description?: string;
  logo_url?: string;
  owner_id: string;
  plan_type?: string;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: "admin" | "manager" | "member" | "viewer";
  joined_at: string;
  user?: {
    id: string;
    username: string;
    display_name?: string;
    avatar_url?: string;
  };
}
