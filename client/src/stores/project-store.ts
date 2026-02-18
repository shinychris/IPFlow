/**
 * 项目状态管理 (Zustand)
 */

import { create } from "zustand";
import { projectsApi } from "@/api/projects";
import type {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectType,
  ProjectStatus,
} from "@/types";

interface ProjectState {
  // 状态
  projects: Project[];
  currentProject: Project | null;
  isLoading: boolean;
  error: string | null;
  total: number;

  // Actions
  fetchProjects: (params?: {
    project_type?: ProjectType;
    status?: ProjectStatus;
    skip?: number;
    limit?: number;
  }) => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  createProject: (data: CreateProjectRequest) => Promise<Project>;
  updateProject: (id: string, data: UpdateProjectRequest) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  duplicateProject: (id: string) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
  clearError: () => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  // 初始状态
  projects: [],
  currentProject: null,
  isLoading: false,
  error: null,
  total: 0,

  // 获取项目列表
  fetchProjects: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const projects = await projectsApi.list(params);
      set({
        projects,
        isLoading: false,
        total: projects.length,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || "获取项目列表失败",
        isLoading: false,
      });
    }
  },

  // 获取单个项目
  fetchProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.getById(id);
      set({
        currentProject: project,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || "获取项目详情失败",
        isLoading: false,
      });
    }
  },

  // 创建项目
  createProject: async (data: CreateProjectRequest) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.create(data);
      set({
        projects: [project, ...get().projects],
        currentProject: project,
        isLoading: false,
        total: get().total + 1,
      });
      return project;
    } catch (error: any) {
      set({
        error: error.response?.data?.message || "创建项目失败",
        isLoading: false,
      });
      throw error;
    }
  },

  // 更新项目
  updateProject: async (id: string, data: UpdateProjectRequest) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.update(id, data);
      set({
        projects: get().projects.map((p) => (p.id === id ? project : p)),
        currentProject: project,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || "更新项目失败",
        isLoading: false,
      });
    }
  },

  // 删除项目
  deleteProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await projectsApi.delete(id);
      set({
        projects: get().projects.filter((p) => p.id !== id),
        currentProject: get().currentProject?.id === id ? null : get().currentProject,
        isLoading: false,
        total: get().total - 1,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || "删除项目失败",
        isLoading: false,
      });
    }
  },

  // 复制项目
  duplicateProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.duplicate(id);
      set({
        projects: [project, ...get().projects],
        isLoading: false,
        total: get().total + 1,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || "复制项目失败",
        isLoading: false,
      });
    }
  },

  // 设置当前项目
  setCurrentProject: (project: Project | null) => {
    set({ currentProject: project });
  },

  // 清除错误
  clearError: () => set({ error: null }),
}));
