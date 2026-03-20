/**
 * 组织状态管理 (Zustand)
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { organizationsApi } from "@/api/organizations";
import type { Organization, OrganizationMember } from "@/types";

interface OrganizationState {
  // 状态
  organizations: Organization[];
  currentOrganization: Organization | null;
  members: OrganizationMember[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchOrganizations: () => Promise<void>;
  setCurrentOrganization: (org: Organization | null) => void;
  createOrganization: (data: {
    name: string;
    slug: string;
    description?: string;
  }) => Promise<Organization>;
  updateOrganization: (id: string, data: Partial<Organization>) => Promise<void>;
  deleteOrganization: (id: string) => Promise<void>;
  fetchMembers: (orgId: string) => Promise<void>;
  inviteMember: (orgId: string, email: string, role: "admin" | "manager" | "member" | "viewer") => Promise<void>;
  removeMember: (orgId: string, memberId: string) => Promise<void>;
  clearError: () => void;
}

export const useOrganizationStore = create<OrganizationState>()(
  persist(
    (set, get) => ({
      // 初始状态
      organizations: [],
      currentOrganization: null,
      members: [],
      isLoading: false,
      error: null,

      // 获取组织列表
      fetchOrganizations: async () => {
        set({ isLoading: true, error: null });
        try {
          const organizations = await organizationsApi.list();
          set({ organizations, isLoading: false });
          
          // 如果没有当前组织，设置第一个为当前
          if (!get().currentOrganization && organizations.length > 0) {
            set({ currentOrganization: organizations[0] });
          }
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "获取组织列表失败",
            isLoading: false,
          });
        }
      },

      // 设置当前组织
      setCurrentOrganization: (org: Organization | null) => {
        set({ currentOrganization: org });
      },

      // 创建组织
      createOrganization: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const organization = await organizationsApi.create(data);
          set({
            organizations: [organization, ...get().organizations],
            currentOrganization: organization,
            isLoading: false,
          });
          return organization;
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "创建组织失败",
            isLoading: false,
          });
          throw error;
        }
      },

      // 更新组织
      updateOrganization: async (id, data) => {
        set({ isLoading: true, error: null });
        try {
          const organization = await organizationsApi.update(id, data);
          set({
            organizations: get().organizations.map((o) =>
              o.id === id ? organization : o
            ),
            currentOrganization:
              get().currentOrganization?.id === id
                ? organization
                : get().currentOrganization,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "更新组织失败",
            isLoading: false,
          });
        }
      },

      // 删除组织
      deleteOrganization: async (id) => {
        set({ isLoading: true, error: null });
        try {
          await organizationsApi.delete(id);
          const remaining = get().organizations.filter((o) => o.id !== id);
          set({
            organizations: remaining,
            currentOrganization:
              get().currentOrganization?.id === id
                ? remaining[0] || null
                : get().currentOrganization,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "删除组织失败",
            isLoading: false,
          });
        }
      },

      // 获取成员列表
      fetchMembers: async (orgId) => {
        set({ isLoading: true, error: null });
        try {
          const members = await organizationsApi.getMembers(orgId);
          set({ members, isLoading: false });
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "获取成员列表失败",
            isLoading: false,
          });
        }
      },

      // 邀请成员
      inviteMember: async (orgId, email, role) => {
        set({ isLoading: true, error: null });
        try {
          await organizationsApi.inviteMember(orgId, { email, role });
          set({ isLoading: false });
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "邀请成员失败",
            isLoading: false,
          });
          throw error;
        }
      },

      // 移除成员
      removeMember: async (orgId, memberId) => {
        set({ isLoading: true, error: null });
        try {
          await organizationsApi.removeMember(orgId, memberId);
          set({
            members: get().members.filter((m) => m.id !== memberId),
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.message || "移除成员失败",
            isLoading: false,
          });
        }
      },

      // 清除错误
      clearError: () => set({ error: null }),
    }),
    {
      name: "organization-storage",
      partialize: (state) => ({
        currentOrganization: state.currentOrganization,
      }),
    }
  )
);
