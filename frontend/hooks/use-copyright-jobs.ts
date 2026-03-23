import { useMutation, useQuery } from "@tanstack/react-query";

import {
  exportJobsApi,
  generationJobsApi,
  type StartGenerationPayload,
} from "@/api/copyright";
import { patentGenerationJobsApi } from "@/api/patents";
import { trademarkGenerationJobsApi } from "@/api/trademarks";

export function useGenerationJob(jobId?: string) {
  return useQuery({
    queryKey: [`/api/v1/copyright/generation-jobs/${jobId}`],
    queryFn: () => generationJobsApi.getById(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "queued"
        ? 1500
        : false,
  });
}

export function useStartGeneration(projectId: string) {
  return useMutation({
    mutationFn: (payload: StartGenerationPayload) =>
      generationJobsApi.start(projectId, payload),
  });
}

export function useExportJob(jobId?: string) {
  return useQuery({
    queryKey: [`/api/v1/copyright/export-jobs/${jobId}`],
    queryFn: () => exportJobsApi.getById(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "queued"
        ? 1500
        : false,
  });
}

export function usePatentGenerationJob(jobId?: string) {
  return useQuery({
    queryKey: [`/api/v1/patents/generation-jobs/${jobId}`],
    queryFn: () => patentGenerationJobsApi.getById(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "queued"
        ? 1500
        : false,
  });
}

export function useTrademarkGenerationJob(jobId?: string) {
  return useQuery({
    queryKey: [`/api/v1/trademarks/generation-jobs/${jobId}`],
    queryFn: () => trademarkGenerationJobsApi.getById(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "queued"
        ? 1500
        : false,
  });
}
