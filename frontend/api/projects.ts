/**
 * 项目相关 API
 */

import { get, post, patch, del } from "./client";
import type {
  ApiResponse,
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
} from "@/types";

export const projectsApi = {
  /**
   * 获取项目列表
   */
  list: (params?: {
    project_type?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<Project[]> =>
    get("/projects", params),

  /**
   * 获取项目详情
   */
  getById: (id: string): Promise<Project> =>
    get(`/projects/${id}`),

  /**
   * 创建项目
   */
  create: (data: CreateProjectRequest): Promise<Project> =>
    post("/projects", data),

  /**
   * 更新项目
   */
  update: (id: string, data: UpdateProjectRequest): Promise<Project> =>
    patch(`/projects/${id}`, data),

  /**
   * 删除项目
   */
  delete: (id: string): Promise<void> =>
    del(`/projects/${id}`),

  /**
   * 复制项目
   */
  duplicate: (id: string): Promise<Project> =>
    post(`/projects/${id}/duplicate`, {}),
};
