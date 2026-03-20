/**
 * 支付 API 客户端
 * Payment API client
 */
import api from "./client";

export interface CreatePaymentRequest {
  planId: string;
  billingInterval: "monthly" | "yearly";
  paymentMethod: "wechat" | "alipay";
  successUrl?: string;
  cancelUrl?: string;
}

export interface PaymentOrder {
  id: string;
  orderNo: string;
  amount: number;
  currency: string;
  status: "pending" | "processing" | "completed" | "failed" | "cancelled";
  paymentMethod: "wechat" | "alipay";
  qrCode?: string; // 微信支付二维码
  payUrl?: string; // 支付宝跳转链接
  expiresAt: string;
  plan: {
    id: string;
    name: string;
  };
}

export interface PaymentStatus {
  orderId: string;
  status: PaymentOrder["status"];
  paidAt?: string;
}

/**
 * 创建支付订单
 */
export async function createPayment(
  data: CreatePaymentRequest
): Promise<PaymentOrder> {
  const response = await api.post("/payments/create", {
    plan_id: data.planId,
    billing_interval: data.billingInterval,
    payment_method: data.paymentMethod,
    success_url: data.successUrl,
    cancel_url: data.cancelUrl,
  });
  const raw = response.data;
  return {
    id: raw.id,
    orderNo: raw.order_no,
    amount: raw.amount,
    currency: raw.currency,
    status: raw.status,
    paymentMethod: raw.payment_method,
    qrCode: raw.qr_code,
    payUrl: raw.pay_url,
    expiresAt: raw.expires_at,
    plan: raw.plan,
  };
}

/**
 * 查询支付状态
 */
export async function getPaymentStatus(
  orderId: string
): Promise<PaymentStatus> {
  const response = await api.get(`/payments/${orderId}/status`);
  const raw = response.data;
  return {
    orderId: raw.order_id,
    status: raw.status,
    paidAt: raw.paid_at,
  };
}

/**
 * 轮询支付状态（用于微信支付扫码后）
 */
export async function pollPaymentStatus(
  orderId: string,
  onUpdate: (status: PaymentStatus) => void,
  maxAttempts = 60
): Promise<void> {
  let attempts = 0;

  const poll = async () => {
    attempts++;

    try {
      const status = await getPaymentStatus(orderId);
      onUpdate(status);

      // 如果支付完成或失败，停止轮询
      if (status.status === "completed" || status.status === "failed") {
        return;
      }

      // 如果订单过期，停止轮询
      if (attempts >= maxAttempts) {
        return;
      }

      // 继续轮询（每2秒一次）
      setTimeout(poll, 2000);
    } catch (error) {
      console.error("Polling payment status error:", error);
      // 出错也继续轮询
      if (attempts < maxAttempts) {
        setTimeout(poll, 2000);
      }
    }
  };

  poll();
}
