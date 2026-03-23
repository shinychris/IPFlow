import { apiRequest } from "@/lib/queryClient";
import type { Project } from "@shared/types";
import { exportJobsApi } from "@/api/copyright";
import { patentExportJobsApi } from "@/api/patents";
import { trademarkExportJobsApi } from "@/api/trademarks";

export type ProjectTypeValue = "copyright" | "patent" | "trademark";

export function resolveProjectType(project: Project): ProjectTypeValue {
  const rawType = (project as any).project_type ?? (project as any).type;
  if (rawType === "patent" || rawType === "trademark") return rawType;
  return "copyright";
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiRequest("DELETE", `/api/v1/projects/${projectId}`);
}

function getExportPath(projectId: string, projectType: ProjectTypeValue): string {
  if (projectType === "patent") return `/api/v1/patents/projects/${projectId}/export`;
  if (projectType === "trademark") return `/api/v1/trademarks/projects/${projectId}/export`;
  return `/api/v1/copyright/projects/${projectId}/export`;
}

function getFilenameFromDisposition(disposition: string | null): string {
  if (!disposition) return "export.zip";
  const matches = disposition.match(/filename="?([^"]+)"?/i);
  return matches?.[1] ?? "export.zip";
}

export async function exportProject(project: Project): Promise<void> {
  const projectId = project.id;
  const projectType = resolveProjectType(project);
  if (projectType === "copyright") {
    const startResult = await exportJobsApi.start(projectId);
    const exportJobId = (startResult.export_job_id ?? startResult.id) as string | undefined;
    if (!exportJobId) {
      throw new Error("导出任务创建失败");
    }
    const detail = await exportJobsApi.getById(exportJobId);
    if (detail.status !== "succeeded" || !detail.download_url) {
      throw new Error(detail.error || "导出任务尚未完成");
    }

    const response = await apiRequest("GET", detail.download_url);
    const fileBlob = await response.blob();
    const filename = getFilenameFromDisposition(response.headers.get("content-disposition"));
    const objectUrl = URL.createObjectURL(fileBlob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
    return;
  }

  if (projectType === "patent") {
    const startResult = await patentExportJobsApi.start(projectId);
    const exportJobId = (startResult.export_job_id ?? startResult.id) as string | undefined;
    if (!exportJobId) throw new Error("导出任务创建失败");
    const detail = await patentExportJobsApi.getById(exportJobId);
    if (detail.status !== "succeeded" || !detail.download_url) {
      throw new Error(detail.error || "导出任务尚未完成");
    }
    const response = await apiRequest("GET", detail.download_url);
    const fileBlob = await response.blob();
    const filename = getFilenameFromDisposition(response.headers.get("content-disposition"));
    const objectUrl = URL.createObjectURL(fileBlob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
    return;
  }

  if (projectType === "trademark") {
    const startResult = await trademarkExportJobsApi.start(projectId);
    const exportJobId = (startResult.export_job_id ?? startResult.id) as string | undefined;
    if (!exportJobId) throw new Error("导出任务创建失败");
    const detail = await trademarkExportJobsApi.getById(exportJobId);
    if (detail.status !== "succeeded" || !detail.download_url) {
      throw new Error(detail.error || "导出任务尚未完成");
    }
    const response = await apiRequest("GET", detail.download_url);
    const fileBlob = await response.blob();
    const filename = getFilenameFromDisposition(response.headers.get("content-disposition"));
    const objectUrl = URL.createObjectURL(fileBlob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
    return;
  }

  const response = await apiRequest("POST", getExportPath(projectId, projectType));
  const fileBlob = await response.blob();
  const filename = getFilenameFromDisposition(response.headers.get("content-disposition"));

  const objectUrl = URL.createObjectURL(fileBlob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}
