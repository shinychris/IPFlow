/**
 * 支付状态管理
 * Payment state management with Zustand
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PaymentState {
  // 弹窗状态
  isOpen: boolean;
  selectedPlan: string | null;
  billingInterval: "monthly" | "yearly";

  // 操作
  openPayment: (planId: string) => void;
  closePayment: () => void;
  setBillingInterval: (interval: "monthly" | "yearly") => void;
}

export const usePaymentStore = create<PaymentState>()(
  persist(
    (set) => ({
      isOpen: false,
      selectedPlan: null,
      billingInterval: "yearly",

      openPayment: (planId) =>
        set({ isOpen: true, selectedPlan: planId }),

      closePayment: () =>
        set({ isOpen: false, selectedPlan: null }),

      setBillingInterval: (interval) =>
        set({ billingInterval: interval }),
    }),
    {
      name: "payment-storage",
      partialize: (state) => ({
        billingInterval: state.billingInterval,
      }),
    }
  )
);
