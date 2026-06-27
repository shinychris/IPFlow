/**
 * 管理后台 API 客户端
 *
 * 对齐 backend /api/v1/admin/*（仅超级管理员可访问）
 */

import { get, patch, del } from "./client";
import type {
  DashboardStats,
  AdminUser,
  AdminOrganization,
  AdminPlan,
  AdminAuditLog,
} from "@/types/admin";

export const adminApi = {
  /** 仪表盘统计 */
  getDashboard: (): Promise<DashboardStats> => get("/admin/dashboard"),

  /** 用户管理 */
  listUsers: (params?: {
    page?: number;
    per_page?: number;
    search?: string;
  }): Promise<AdminUser[]> =>
    get("/admin/users", params),
  updateUser: (
    userId: string,
    data: Partial<Pick<AdminUser, "role" | "status" | "display_name">>,
  ): Promise<AdminUser> => patch(`/admin/users/${userId}`, data),
  deleteUser: (userId: string): Promise<void> => del(`/admin/users/${userId}`),

  /** 组织管理 */
  listOrganizations: (params?: {
    page?: number;
    per_page?: number;
    search?: string;
  }): Promise<AdminOrganization[]> =>
    get("/admin/organizations", params),
  updateOrganization: (
    orgId: string,
    data: Partial<AdminOrganization>,
  ): Promise<AdminOrganization> =>
    patch(`/admin/organizations/${orgId}`, data),
  deleteOrganization: (orgId: string): Promise<void> =>
    del(`/admin/organizations/${orgId}`),

  /** 计划管理 */
  listPlans: (): Promise<AdminPlan[]> => get("/admin/plans"),
  updatePlan: (planId: string, data: Partial<AdminPlan>): Promise<AdminPlan> =>
    patch(`/admin/plans/${planId}`, data),
  deletePlan: (planId: string): Promise<void> => del(`/admin/plans/${planId}`),

  /** 审计日志 */
  listAuditLogs: (params?: {
    page?: number;
    per_page?: number;
  }): Promise<AdminAuditLog[]> => get("/admin/audit-logs", params),
};
