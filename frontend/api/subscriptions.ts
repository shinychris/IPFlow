/**
 * 订阅与计费 API 客户端
 *
 * 对齐 backend /api/v1/subscriptions/*
 */

import { get, post, patch } from "./client";

export interface Plan {
  id: string;
  name: string;
  description?: string | null;
  price_monthly?: number | null;
  price_yearly?: number | null;
  limits?: Record<string, number | null> | null;
  is_active?: boolean;
}

export interface Subscription {
  id: string;
  plan_id: string;
  plan?: Plan | null;
  status?: string;
  interval?: string | null;
  current_period_end?: string | null;
  cancel_at_period_end?: boolean;
}

export interface Invoice {
  id: string;
  amount?: number | null;
  currency?: string | null;
  status?: string | null;
  created_at?: string | null;
  period_start?: string | null;
  period_end?: string | null;
}

export interface UsageStats {
  projects?: { used: number; limit: number | null };
  storage?: { used: number; limit: number | null };
  members?: { used: number; limit: number | null };
  [key: string]: unknown;
}

export const subscriptionsApi = {
  /** 订阅计划列表 */
  listPlans: (): Promise<Plan[]> => get("/subscriptions/plans"),

  /** 获取单个计划 */
  getPlan: (planId: string): Promise<Plan> =>
    get(`/subscriptions/plans/${planId}`),

  /** 当前订阅 */
  getCurrent: (): Promise<Subscription | null> =>
    get("/subscriptions/current"),

  /** 创建/切换订阅 */
  create: (data: {
    plan_id: string;
    interval?: "monthly" | "yearly";
  }): Promise<Subscription> => post("/subscriptions", data),

  /** 更新订阅 */
  update: (data: {
    plan_id?: string;
    cancel_at_period_end?: boolean;
  }): Promise<Subscription> => patch("/subscriptions", data),

  /** 取消订阅 */
  cancel: (atPeriodEnd = true): Promise<Subscription> =>
    post("/subscriptions/cancel", null, {
      params: { at_period_end: atPeriodEnd },
    }),

  /** 发票/账单记录 */
  listInvoices: (): Promise<Invoice[]> => get("/subscriptions/invoices"),

  /** 使用量统计 */
  getUsage: (): Promise<UsageStats> => get("/subscriptions/usage"),
};
