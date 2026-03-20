/**
 * API 模块导出
 */

export { default as apiClient, get, post, put, patch, del, uploadFile } from "./client";
export { authApi } from "./auth";
export { projectsApi } from "./projects";
export {
  softwareInfoApi,
  codeBundlesApi,
  manualsApi,
  complianceApi,
  exportApi,
} from "./copyright";
export {
  patentInfoApi,
  patentClaimsApi,
  patentDescriptionApi,
  patentProofAssetsApi,
  patentComplianceApi,
  patentExportApi,
  type PatentInfoRequest,
  type PatentClaimsRequest,
  type PatentDescriptionRequest,
  type PatentType,
} from "./patents";
export {
  trademarkInfoApi,
  niceClassesApi,
  trademarkImageApi,
  trademarkProofAssetsApi,
  trademarkComplianceApi,
  trademarkExportApi,
  type TrademarkInfoRequest,
  type NiceClassesRequest,
  type TrademarkType,
  type ApplicantType,
} from "./trademarks";
export { organizationsApi } from "./organizations";
export {
  getAIConfig,
  getModels,
  getOllamaModels,
  getProviders,
  chat,
  streamChat,
  type AIConfig,
  type AIModel,
  type AIProvider,
  type ChatRequest,
  type ChatResponse,
} from "./ai-config";
