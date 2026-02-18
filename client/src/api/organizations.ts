/**
 * 组织相关 API
 */

import { get, post, patch, del } from "./client";
import type {
  Organization,
  OrganizationMember,
  ApiResponse,
} from "@/types";

export interface CreateOrganizationRequest {
  name: string;
  slug: string;
  description?: string;
  business_type?: string;
  license_number?: string;
  contact_email?: string;
  contact_phone?: string;
}

export interface UpdateOrganizationRequest {
  name?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
}

export interface InviteMemberRequest {
  email: string;
  role: "admin" | "manager" | "member" | "viewer";
}

export const organizationsApi = {
  /**
   * 获取组织列表
   */
  list: (): Promise<Organization[]> =>
    get("/organizations"),

  /**
   * 获取组织详情
   */
  getById: (id: string): Promise<Organization> =>
    get(`/organizations/${id}`),

  /**
   * 创建组织
   */
  create: (data: CreateOrganizationRequest): Promise<Organization> =>
    post("/organizations", data),

  /**
   * 更新组织
   */
  update: (id: string, data: UpdateOrganizationRequest): Promise<Organization> =>
    patch(`/organizations/${id}`, data),

  /**
   * 删除组织
   */
  delete: (id: string): Promise<void> =>
    del(`/organizations/${id}`),

  /**
   * 获取成员列表
   */
  getMembers: (orgId: string): Promise<OrganizationMember[]> =>
    get(`/organizations/${orgId}/members`),

  /**
   * 邀请成员
   */
  inviteMember: (orgId: string, data: InviteMemberRequest): Promise<{ message: string; email: string }> =>
    post(`/organizations/${orgId}/invite`, data),

  /**
   * 更新成员角色
   */
  updateMemberRole: (orgId: string, memberId: string, role: string): Promise<OrganizationMember> =>
    patch(`/organizations/${orgId}/members/${memberId}`, { role }),

  /**
   * 移除成员
   */
  removeMember: (orgId: string, memberId: string): Promise<void> =>
    del(`/organizations/${orgId}/members/${memberId}`),

  /**
   * 通过邀请链接加入
   */
  joinByInvite: (token: string): Promise<{ message: string; organization_id: string }> =>
    post(`/organizations/join/${token}`, {}),
};
