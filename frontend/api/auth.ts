/**
 * 认证相关 API
 */

import { get, post, put } from "./client";
import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from "@/types";

export const authApi = {
  /**
   * 用户登录
   */
  login: (data: LoginRequest): Promise<ApiResponse<LoginResponse>> =>
    post("/auth/login", data),

  /**
   * 用户注册
   */
  register: (data: RegisterRequest): Promise<ApiResponse<any>> =>
    post("/auth/register", data),

  /**
   * 用户登出
   */
  logout: (): Promise<ApiResponse<null>> =>
    post("/auth/logout", {}),

  /**
   * 刷新令牌
   */
  refreshToken: (refreshToken: string): Promise<ApiResponse<{ access_token: string; expires_in: number }>> =>
    post("/auth/refresh", { refresh_token: refreshToken }),

  /**
   * 获取当前用户信息
   */
  getMe: (): Promise<ApiResponse<User>> =>
    get("/auth/me"),

  /**
   * 更新当前用户资料（昵称、邮箱）
   */
  updateMe: (data: {
    display_name?: string | null;
    email?: string;
  }): Promise<ApiResponse<User>> => put("/auth/me", data),
};
