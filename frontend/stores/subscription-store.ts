import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import api from '@/lib/api';
import type { 
  Plan, 
  Subscription, 
  Invoice, 
  UsageStats,
  PaymentMethod 
} from '@/types/subscription';

interface SubscriptionState {
  // 状态
  plans: Plan[];
  currentSubscription: Subscription | null;
  invoices: Invoice[];
  usageStats: UsageStats | null;
  paymentMethods: PaymentMethod[];
  isLoading: boolean;
  error: string | null;

  // 操作
  fetchPlans: () => Promise<void>;
  fetchCurrentSubscription: () => Promise<void>;
  createSubscription: (planId: string, interval: 'monthly' | 'yearly') => Promise<void>;
  updateSubscription: (data: { planId?: string; cancelAtPeriodEnd?: boolean }) => Promise<void>;
  cancelSubscription: (atPeriodEnd?: boolean) => Promise<void>;
  fetchInvoices: () => Promise<void>;
  fetchUsageStats: () => Promise<void>;
  fetchPaymentMethods: () => Promise<void>;
  clearError: () => void;
}

export const useSubscriptionStore = create<SubscriptionState>()(
  persist(
    (set, get) => ({
      // 初始状态
      plans: [],
      currentSubscription: null,
      invoices: [],
      usageStats: null,
      paymentMethods: [],
      isLoading: false,
      error: null,

      // 获取计划列表
      fetchPlans: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get('/subscriptions/plans');
          set({ plans: response.data, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '获取计划列表失败', 
            isLoading: false 
          });
        }
      },

      // 获取当前订阅
      fetchCurrentSubscription: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get('/subscriptions/current');
          set({ currentSubscription: response.data, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '获取订阅信息失败', 
            isLoading: false 
          });
        }
      },

      // 创建订阅
      createSubscription: async (planId, interval) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/subscriptions', {
            plan_id: planId,
            interval,
          });
          set({ 
            currentSubscription: response.data, 
            isLoading: false 
          });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '创建订阅失败', 
            isLoading: false 
          });
          throw error;
        }
      },

      // 更新订阅
      updateSubscription: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.patch('/subscriptions', data);
          set({ 
            currentSubscription: response.data, 
            isLoading: false 
          });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '更新订阅失败', 
            isLoading: false 
          });
          throw error;
        }
      },

      // 取消订阅
      cancelSubscription: async (atPeriodEnd = true) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/subscriptions/cancel', null, {
            params: { at_period_end: atPeriodEnd },
          });
          set({ 
            currentSubscription: response.data, 
            isLoading: false 
          });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '取消订阅失败', 
            isLoading: false 
          });
          throw error;
        }
      },

      // 获取发票列表
      fetchInvoices: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get('/subscriptions/invoices');
          set({ invoices: response.data, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '获取发票列表失败', 
            isLoading: false 
          });
        }
      },

      // 获取使用统计
      fetchUsageStats: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get('/subscriptions/usage');
          set({ usageStats: response.data, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '获取使用统计失败', 
            isLoading: false 
          });
        }
      },

      // 获取支付方式
      fetchPaymentMethods: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get('/subscriptions/payment-methods');
          set({ paymentMethods: response.data, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || '获取支付方式失败', 
            isLoading: false 
          });
        }
      },

      // 清除错误
      clearError: () => set({ error: null }),
    }),
    {
      name: 'subscription-storage',
      partialize: (state) => ({
        currentSubscription: state.currentSubscription,
      }),
    }
  )
);
