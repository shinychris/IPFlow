/**
 * 商标相关 API（对齐 backend /api/v1/trademarks/*）
 */

import apiClient, { get, post, put } from "./client";

export type TrademarkType = "word" | "device" | "composite" | "3d" | "sound" | "color";
export type ApplicantType = "individual" | "enterprise" | "institution";

export interface TrademarkInfoRequest {
  trademark_type: TrademarkType;
  trademark_name?: string;
  description?: string;
  design_description?: string;
  color_claim?: string;
  special_notes?: string;
}

export interface NiceClassesRequest {
  class_number: number;
  goods_services: string[];
}

export const trademarkInfoApi = {
  get: (projectId: string): Promise<any> =>
    get(`/trademarks/projects/${projectId}/trademark-info`),
  save: (projectId: string, data: TrademarkInfoRequest): Promise<any> =>
    put(`/trademarks/projects/${projectId}/trademark-info`, data),
  update: (projectId: string, data: Partial<TrademarkInfoRequest>): Promise<any> =>
    put(`/trademarks/projects/${projectId}/trademark-info`, data),
};

export const niceClassesApi = {
  listAll: (
    projectId: string,
    params?: { class_number?: number; search?: string; page?: number; page_size?: number }
  ): Promise<any> =>
    get(`/trademarks/projects/${projectId}/nice-classes`, params),
  getSelected: (projectId: string): Promise<any> =>
    get(`/trademarks/projects/${projectId}/nice-classes/selected`),
  addSelected: (projectId: string, data: NiceClassesRequest): Promise<any> =>
    post(`/trademarks/projects/${projectId}/nice-classes/selected`, data),
  updateSelected: (projectId: string, associationId: string, goods_services: string[]): Promise<any> =>
    put(`/trademarks/projects/${projectId}/nice-classes/selected/${associationId}`, { goods_services }),
  removeSelected: async (projectId: string, associationId: string): Promise<void> => {
    await apiClient.delete(`/trademarks/projects/${projectId}/nice-classes/selected/${associationId}`);
  },
};

export const trademarkImageApi = {
  updateUpload: (projectId: string, uploadId: string): Promise<any> =>
    put(`/trademarks/projects/${projectId}/trademark-info/upload?upload_id=${uploadId}`, {}),
};

// 占位：当前后端无商标 proof-assets 独立路由
export const trademarkProofAssetsApi = {
  list: async (_projectId: string): Promise<any[]> => [],
};

export const trademarkComplianceApi = {
  getReport: async (_projectId: string): Promise<any> => ({ results: [] }),
  check: async (_projectId: string): Promise<any> => ({ results: [] }),
};

export const trademarkExportApi = {
  getPreview: (projectId: string): Promise<any> =>
    get(`/trademarks/projects/${projectId}/export/preview`),
  export: async (projectId: string): Promise<Blob> => {
    const response = await apiClient.post(
      `/trademarks/projects/${projectId}/export`,
      {},
      { responseType: "blob" }
    );
    return response.data as Blob;
  },
};

export interface StartTrademarkGenerationPayload {
  generation_mode: "guided_confirm";
  inputs: {
    extra_brief?: string;
    history_reuse?: { enabled: boolean; source_project_ids: string[] };
    org_knowledge?: { enabled: boolean; dataset_ids: string[] };
  };
  policy: { overwrite_strategy: "fill_blank_only" | "new_revision" };
}

export const trademarkGenerationJobsApi = {
  getContext: (projectId: string): Promise<any> =>
    get(`/trademarks/projects/${projectId}/generation-context`),
  start: (projectId: string, data: StartTrademarkGenerationPayload): Promise<any> =>
    post(`/trademarks/projects/${projectId}/generation-jobs`, data),
  getById: (jobId: string): Promise<any> =>
    get(`/trademarks/generation-jobs/${jobId}`),
  listByProject: (projectId: string): Promise<any> =>
    get(`/trademarks/projects/${projectId}/generation-jobs`),
  confirmMaterials: (projectId: string): Promise<any> =>
    post(`/trademarks/projects/${projectId}/materials/confirm`, {}),
};

export const trademarkExportJobsApi = {
  start: (projectId: string): Promise<any> =>
    post(`/trademarks/projects/${projectId}/export-jobs`, {}),
  getById: (jobId: string): Promise<any> =>
    get(`/trademarks/export-jobs/${jobId}`),
  listByProject: (projectId: string): Promise<any> =>
    get(`/trademarks/projects/${projectId}/export-jobs`),
};
