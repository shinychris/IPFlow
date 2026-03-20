import { create } from 'zustand';

import api from '@/lib/api';
import type { 
  DashboardStats,
  AdminUser,
  AdminOrganization,
  AdminPlan,
  AdminAuditLog,
} from '@/types/admin';

interface AdminState {
  // 状态
  dashboardStats: DashboardStats | null;
  users: AdminUser[];
  organizations: AdminOrganization[];
  plans: AdminPlan[];
  auditLogs: AdminAuditLog[];
  isLoading: boolean;
  error: string | null;
  
  // 分页
  pagination: {
    page: number;
    perPage: number;
    total: number;
  };

  // 操作
  fetchDashboardStats: () => Promise<void>;
  fetchUsers: (page?: number, perPage?: number, search?: string) => Promise<void>;
  updateUser: (userId: string, data: Partial<AdminUser>) => Promise<void>;
  deleteUser: (userId: string) => Promise<void>;
  fetchOrganizations: (page?: number, perPage?: number, search?: string) => Promise<void>;
  updateOrganization: (orgId: string, data: Partial<AdminOrganization>) => Promise<void>;
  deleteOrganization: (orgId: string) => Promise<void>;
  fetchPlans: () => Promise<void>;
  createPlan: (data: Omit<AdminPlan, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updatePlan: (planId: string, data: Partial<AdminPlan>) => Promise<void>;
  deletePlan: (planId: string) => Promise<void>;
  fetchAuditLogs: (page?: number, perPage?: number) => Promise<void>;
  clearError: () => void;
}

export const useAdminStore = create<AdminState>((set, get) => ({
  // 初始状态
  dashboardStats: null,
  users: [],
  organizations: [],
  plans: [],
  auditLogs: [],
  isLoading: false,
  error: null,
  pagination: {
    page: 1,
    perPage: 20,
    total: 0,
  },

  // 获取仪表盘统计
  fetchDashboardStats: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get('/admin/dashboard');
      set({ dashboardStats: response.data, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '获取统计数据失败', 
        isLoading: false 
      });
    }
  },

  // 获取用户列表
  fetchUsers: async (page = 1, perPage = 20, search = '') => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get('/admin/users', {
        params: { page, per_page: perPage, search },
      });
      set({ 
        users: response.data, 
        pagination: { ...get().pagination, page, perPage },
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '获取用户列表失败', 
        isLoading: false 
      });
    }
  },

  // 更新用户
  updateUser: async (userId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.patch(`/admin/users/${userId}`, data);
      const users = get().users.map(u => u.id === userId ? response.data : u);
      set({ users, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '更新用户失败', 
        isLoading: false 
      });
      throw error;
    }
  },

  // 删除用户
  deleteUser: async (userId) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/admin/users/${userId}`);
      const users = get().users.filter(u => u.id !== userId);
      set({ users, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '删除用户失败', 
        isLoading: false 
      });
      throw error;
    }
  },

  // 获取组织列表
  fetchOrganizations: async (page = 1, perPage = 20, search = '') => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get('/admin/organizations', {
        params: { page, per_page: perPage, search },
      });
      set({ 
        organizations: response.data, 
        pagination: { ...get().pagination, page, perPage },
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '获取组织列表失败', 
        isLoading: false 
      });
    }
  },

  // 更新组织
  updateOrganization: async (orgId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.patch(`/admin/organizations/${orgId}`, data);
      const organizations = get().organizations.map(o => o.id === orgId ? response.data : o);
      set({ organizations, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '更新组织失败', 
        isLoading: false 
      });
      throw error;
    }
  },

  // 删除组织
  deleteOrganization: async (orgId) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/admin/organizations/${orgId}`);
      const organizations = get().organizations.filter(o => o.id !== orgId);
      set({ organizations, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '删除组织失败', 
        isLoading: false 
      });
      throw error;
    }
  },

  // 获取计划列表
  fetchPlans: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get('/admin/plans');
      set({ plans: response.data, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '获取计划列表失败', 
        isLoading: false 
      });
    }
  },

  // 创建计划
  createPlan: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/admin/plans', data);
      set({ 
        plans: [...get().plans, response.data], 
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '创建计划失败', 
        isLoading: false 
      });
      throw error;
    }
  },

  // 更新计划
  updatePlan: async (planId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.patch(`/admin/plans/${planId}`, data);
      const plans = get().plans.map(p => p.id === planId ? response.data : p);
      set({ plans, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '更新计划失败', 
        isLoading: false 
      });
      throw error;
    }
  },

  // 删除计划
  deletePlan: async (planId) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/admin/plans/${planId}`);
      const plans = get().plans.filter(p => p.id !== planId);
      set({ plans, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '删除计划失败', 
        isLoading: false 
      });
      throw error;
    }
  },

  // 获取审计日志
  fetchAuditLogs: async (page = 1, perPage = 50) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get('/admin/audit-logs', {
        params: { page, per_page: perPage },
      });
      set({ 
        auditLogs: response.data, 
        pagination: { ...get().pagination, page, perPage },
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || '获取审计日志失败', 
        isLoading: false 
      });
    }
  },

  // 清除错误
  clearError: () => set({ error: null }),
}));
