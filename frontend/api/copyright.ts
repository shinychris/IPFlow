/**
 * 软著相关 API
 */

import apiClient, { get, post, put, del, uploadFile } from "./client";
import type {
  CopyrightData,
  CodeBundle,
  CopyrightManual,
  SoftwareInfoRequest,
  CreateManualRequest,
  ComplianceReport,
  ExportPreview,
  GenerationContext,
  GenerationJob,
  ExportJob,
} from "@/types";

// 软件信息 API
export const softwareInfoApi = {
  /**
   * 获取软件信息
   */
  get: (projectId: string): Promise<CopyrightData> =>
    get(`/copyright/projects/${projectId}/software-info`),

  /**
   * 更新软件信息
   */
  update: (projectId: string, data: SoftwareInfoRequest): Promise<CopyrightData> =>
    put(`/copyright/projects/${projectId}/software-info`, data),
};

// 代码包 API
export const codeBundlesApi = {
  /**
   * 获取代码包列表
   */
  list: (projectId: string): Promise<{ items: CodeBundle[]; total: number }> =>
    get(`/copyright/projects/${projectId}/code-bundles`),

  /**
   * 上传代码包
   */
  upload: (
    projectId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<CodeBundle> =>
    uploadFile(`/copyright/projects/${projectId}/code-bundles`, file, onProgress),

  /**
   * 获取代码包详情
   */
  getById: (projectId: string, bundleId: string): Promise<CodeBundle> =>
    get(`/copyright/projects/${projectId}/code-bundles/${bundleId}`),

  /**
   * 删除代码包
   */
  delete: (projectId: string, bundleId: string): Promise<void> =>
    del(`/copyright/projects/${projectId}/code-bundles/${bundleId}`),

  /**
   * 预览代码包指定页
   */
  preview: (projectId: string, bundleId: string, page: number): Promise<any> =>
    get(`/copyright/projects/${projectId}/code-bundles/${bundleId}/preview`, { page }),
};

// 说明书 API
export const manualsApi = {
  /**
   * 获取说明书列表
   */
  list: (projectId: string): Promise<{ items: CopyrightManual[]; total: number }> =>
    get(`/copyright/projects/${projectId}/manuals`),

  /**
   * 创建说明书
   */
  create: (projectId: string, data: CreateManualRequest): Promise<CopyrightManual> =>
    post(`/copyright/projects/${projectId}/manuals`, data),

  /**
   * 获取说明书详情
   */
  getById: (projectId: string, manualId: string): Promise<CopyrightManual> =>
    get(`/copyright/projects/${projectId}/manuals/${manualId}`),

  /**
   * 更新说明书
   */
  update: (projectId: string, manualId: string, data: Partial<CreateManualRequest>): Promise<CopyrightManual> =>
    put(`/copyright/projects/${projectId}/manuals/${manualId}`, data),

  /**
   * 删除说明书
   */
  delete: (projectId: string, manualId: string): Promise<void> =>
    del(`/copyright/projects/${projectId}/manuals/${manualId}`),

  /**
   * 获取说明书统计
   */
  getStats: (projectId: string, manualId: string): Promise<any> =>
    get(`/copyright/projects/${projectId}/manuals/${manualId}/stats`),
};

// 合规检查 API
export const complianceApi = {
  /**
   * 获取合规检查结果
   */
  getReport: (projectId: string): Promise<ComplianceReport> =>
    get(`/compliance/projects/${projectId}`),

  /**
   * 执行合规检查
   */
  check: (projectId: string): Promise<ComplianceReport> =>
    post(`/compliance/projects/${projectId}/check`, {}),
};

// 导出 API
export const exportApi = {
  /**
   * 获取导出预览
   */
  getPreview: (projectId: string): Promise<ExportPreview> =>
    get(`/copyright/projects/${projectId}/export/preview`),

  /**
   * 导出项目
   * 返回 Blob 数据，需要前端处理下载
   */
  export: async (projectId: string): Promise<Blob> => {
    const response = await apiClient.post(
      `/copyright/projects/${projectId}/export`,
      {},
      { responseType: "blob" }
    );
    return response.data as Blob;
  },
};

export interface StartGenerationPayload {
  generation_mode: "guided_confirm";
  inputs: {
    extra_brief?: string;
    repo?: { provider?: string; url?: string; branch?: string; auth_ref?: string };
    history_reuse?: { enabled: boolean; source_project_ids: string[] };
    org_knowledge?: { enabled: boolean; dataset_ids: string[] };
  };
  policy: { overwrite_strategy: "fill_blank_only" | "new_revision" };
}

export const generationJobsApi = {
  getContext: (projectId: string): Promise<GenerationContext> =>
    get(`/copyright/projects/${projectId}/generation-context`),

  start: (projectId: string, data: StartGenerationPayload): Promise<GenerationJob> =>
    post(`/copyright/projects/${projectId}/generation-jobs`, data),

  getById: (jobId: string): Promise<GenerationJob> =>
    get(`/copyright/generation-jobs/${jobId}`),

  listByProject: (projectId: string): Promise<{ items: GenerationJob[]; total: number }> =>
    get(`/copyright/projects/${projectId}/generation-jobs`),

  confirmMaterials: (projectId: string): Promise<{ flow_status: string }> =>
    post(`/copyright/projects/${projectId}/materials/confirm`, {}),
};

export const exportJobsApi = {
  start: (projectId: string): Promise<ExportJob> =>
    post(`/copyright/projects/${projectId}/export-jobs`, {}),

  getById: (jobId: string): Promise<ExportJob> =>
    get(`/copyright/export-jobs/${jobId}`),

  listByProject: (projectId: string): Promise<{ items: ExportJob[]; total: number }> =>
    get(`/copyright/projects/${projectId}/export-jobs`),
};
