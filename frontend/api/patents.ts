/**
 * 专利相关 API（对齐 backend /api/v1/patents/*）
 */

import apiClient, { get, post, put } from "./client";

export type PatentType = "invention" | "utility_model" | "design";

export interface PatentInfoRequest {
  patent_type: PatentType;
  title: string;
  technical_field?: string;
  background_art?: string;
  abstract?: string;
  abstract_figure_number?: string;
}

export interface PatentClaimsRequest {
  claim_number: number;
  claim_type: "independent" | "dependent";
  parent_claim_number?: number;
  content: string;
}

export interface PatentDescriptionRequest {
  technical_field?: string;
  background_art?: string;
  invention_content?: {
    problem_solved?: string;
    technical_solution?: string;
    beneficial_effects?: string;
  };
  implementation?: string;
}

export const patentInfoApi = {
  get: (projectId: string): Promise<any> =>
    get(`/patents/projects/${projectId}/patent-info`),
  save: (projectId: string, data: PatentInfoRequest): Promise<any> =>
    put(`/patents/projects/${projectId}/patent-info`, data),
  update: (projectId: string, data: Partial<PatentInfoRequest>): Promise<any> =>
    put(`/patents/projects/${projectId}/patent-info`, data),
};

export const patentClaimsApi = {
  list: (projectId: string): Promise<any> =>
    get(`/patents/projects/${projectId}/claims`),
  create: (projectId: string, data: PatentClaimsRequest): Promise<any> =>
    post(`/patents/projects/${projectId}/claims`, data),
  update: (projectId: string, claimId: string, data: Partial<PatentClaimsRequest>): Promise<any> =>
    put(`/patents/projects/${projectId}/claims/${claimId}`, data),
  delete: async (projectId: string, claimId: string): Promise<void> => {
    await apiClient.delete(`/patents/projects/${projectId}/claims/${claimId}`);
  },
};

export const patentDescriptionApi = {
  get: (projectId: string): Promise<any> =>
    get(`/patents/projects/${projectId}/description`),
  update: (projectId: string, data: PatentDescriptionRequest): Promise<any> =>
    put(`/patents/projects/${projectId}/description`, data),
  preview: (projectId: string): Promise<any> =>
    get(`/patents/projects/${projectId}/description/preview`),
};

// 占位，当前后端未提供专利 proof-assets 专用接口
export const patentProofAssetsApi = {
  list: async (_projectId: string): Promise<any[]> => [],
};

// 占位，当前后端未提供专利合规独立路由
export const patentComplianceApi = {
  getReport: async (_projectId: string): Promise<any> => ({ results: [] }),
  check: async (_projectId: string): Promise<any> => ({ results: [] }),
};

export const patentExportApi = {
  getPreview: (projectId: string): Promise<any> =>
    get(`/patents/projects/${projectId}/export/preview`),
  export: async (projectId: string): Promise<Blob> => {
    const response = await apiClient.post(
      `/patents/projects/${projectId}/export`,
      {},
      { responseType: "blob" }
    );
    return response.data as Blob;
  },
};
