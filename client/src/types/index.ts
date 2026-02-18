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
}

export interface Project {
  id: string;
  owner_id: string;
  project_type: ProjectType;
  status: ProjectStatus;
  current_step: number;
  name: string;
  version: string;
  description?: string;
  subject_type: SubjectType;
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
  created_at: string;
  updated_at: string;
}

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
  category: "info" | "code" | "manual" | "proof";
  status: "passed" | "warning" | "failed" | "skipped";
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
  software_info: {
    has_data: boolean;
    software_name?: string;
  };
  code_bundle: {
    has_data: boolean;
    total_pages: number;
    has_enough_code: boolean;
  };
  manual: {
    has_data: boolean;
    page_count: number;
  };
  files_in_package: string[];
}
