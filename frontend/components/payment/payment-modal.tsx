/**
 * 支付弹窗组件
 * Payment modal - handle subscription purchase
 */
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { usePaymentStore } from "@/stores/payment-store";
import { createPayment, pollPaymentStatus, type PaymentOrder } from "@/api/payments";
import { Loader2, QrCode, ExternalLink } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";

const PLAN_PRICES = {
  single: { monthly: 19, yearly: 19 },
  starter: { monthly: 49, yearly: 490 },
  professional: { monthly: 199, yearly: 1990 },
};

export function PaymentModal() {
  const { isOpen, selectedPlan, closePayment } = usePaymentStore();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();

  const [billingInterval, setBillingInterval] = useState<"monthly" | "yearly">("yearly");
  const [paymentMethod, setPaymentMethod] = useState<"wechat" | "alipay">("wechat");
  const [isLoading, setIsLoading] = useState(false);
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const isSinglePlan = selectedPlan === "single";

  // 计算价格
  const price = selectedPlan
    ? PLAN_PRICES[selectedPlan as keyof typeof PLAN_PRICES]?.[billingInterval]
    : 0;
  const displayPrice = price ?? 0;

  useEffect(() => {
    if (isSinglePlan) {
      setBillingInterval("monthly");
    }
  }, [isSinglePlan]);

  // 当弹窗关闭时重置状态
  useEffect(() => {
    if (!isOpen) {
      setPaymentOrder(null);
      setIsPolling(false);
    }
  }, [isOpen]);

  // 打开弹窗时检查登录状态
  useEffect(() => {
    if (isOpen && !isAuthenticated) {
      closePayment();
      router.push("/login?redirect=" + encodeURIComponent("/pricing"));
    }
  }, [isOpen, isAuthenticated]);

  const handleCreatePayment = async () => {
    if (!selectedPlan) return;

    setIsLoading(true);
    try {
      const order = await createPayment({
        planId: selectedPlan,
        billingInterval,
        paymentMethod,
        successUrl: `${window.location.origin}/dashboard?payment=success`,
        cancelUrl: `${window.location.origin}/pricing?payment=cancelled`,
      });

      setPaymentOrder(order);

      // 如果是微信支付，开始轮询支付状态
      if (paymentMethod === "wechat") {
        setIsPolling(true);
        pollPaymentStatus(order.id, (status) => {
          if (status.status === "completed") {
            setIsPolling(false);
            toast({
              title: "支付成功",
              description: "感谢您的订阅！正在跳转...",
            });
            setTimeout(() => {
              closePayment();
              router.push("/dashboard");
            }, 1500);
          } else if (status.status === "failed") {
            setIsPolling(false);
            toast({
              title: "支付失败",
              description: "支付未完成，请重试",
              variant: "destructive",
            });
          }
        });
      }
    } catch (error: any) {
      toast({
        title: "创建支付订单失败",
        description: error.message || "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAlipayRedirect = () => {
    if (paymentOrder?.payUrl) {
      window.open(paymentOrder.payUrl, "_blank");
      // 开始轮询支付状态
      setIsPolling(true);
      pollPaymentStatus(paymentOrder.id, (status) => {
        if (status.status === "completed") {
          setIsPolling(false);
          toast({
            title: "支付成功",
            description: "感谢您的订阅！",
          });
          closePayment();
          router.push("/dashboard");
        }
      });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={closePayment}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>完成订阅</DialogTitle>
          <DialogDescription>
            选择您的订阅计划并完成支付
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* 计费周期选择 */}
          {!isSinglePlan ? (
            <div className="space-y-3">
              <Label>计费周期</Label>
              <Tabs
                value={billingInterval}
                onValueChange={(v: any) => setBillingInterval(v)}
                className="w-full"
              >
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="monthly">月付</TabsTrigger>
                  <TabsTrigger value="yearly">
                    年付
                    <span className="ml-1 text-xs text-green-600 dark:text-green-400">
                      (省17%)
                    </span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          ) : (
            <div className="space-y-2">
              <Label>计费方式</Label>
              <div className="rounded-md border px-3 py-2 text-sm text-muted-foreground">
                按次付费（单次结算）
              </div>
            </div>
          )}

          {/* 价格显示 */}
          <div className="text-center p-6 bg-muted rounded-lg">
            <div className="text-3xl font-bold">¥{isSinglePlan ? displayPrice.toFixed(1) : displayPrice}</div>
            <div className="text-sm text-muted-foreground mt-1">
              {isSinglePlan ? "每次" : billingInterval === "monthly" ? "每月" : "每年"}
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              未通过可联系客服退款
            </div>
          </div>

          {/* 支付方式选择 */}
          {!paymentOrder && (
            <div className="space-y-3">
              <Label>支付方式</Label>
              <RadioGroup
                value={paymentMethod}
                onValueChange={(v: any) => setPaymentMethod(v)}
              >
                <div className="flex items-center space-x-2 border p-3 rounded-lg hover:bg-accent/50 cursor-pointer">
                  <RadioGroupItem value="wechat" id="wechat" />
                  <Label htmlFor="wechat" className="flex-1 cursor-pointer">
                    微信支付
                  </Label>
                </div>
                <div className="flex items-center space-x-2 border p-3 rounded-lg hover:bg-accent/50 cursor-pointer">
                  <RadioGroupItem value="alipay" id="alipay" />
                  <Label htmlFor="alipay" className="flex-1 cursor-pointer">
                    支付宝
                  </Label>
                </div>
              </RadioGroup>
            </div>
          )}

          {/* 微信支付二维码 */}
          {paymentOrder && paymentMethod === "wechat" && paymentOrder.qrCode && (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-sm mb-4">请使用微信扫码支付</p>
                <div className="flex justify-center">
                  <div className="border-4 border-primary p-2 rounded-lg bg-white">
                    <QrCode className="h-48 w-48 text-black" />
                  </div>
                </div>
                {isPolling && (
                  <div className="flex items-center justify-center gap-2 mt-4 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>等待支付中...</span>
                  </div>
                )}
                <div className="text-xs text-muted-foreground mt-2">
                  订单号：{paymentOrder.orderNo}
                </div>
              </div>
            </div>
          )}

          {/* 支付宝跳转 */}
          {paymentOrder && paymentMethod === "alipay" && paymentOrder.payUrl && (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-sm mb-4">点击下方按钮跳转到支付宝完成支付</p>
                <Button
                  onClick={handleAlipayRedirect}
                  className="w-full"
                  size="lg"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  前往支付宝支付
                </Button>
                {isPolling && (
                  <div className="flex items-center justify-center gap-2 mt-4 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>等待支付中...</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={closePayment}
            disabled={isLoading || isPolling}
            className="flex-1"
          >
            取消
          </Button>
          {!paymentOrder && (
            <Button
              onClick={handleCreatePayment}
              disabled={isLoading || isPolling}
              className="flex-1"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  创建订单中...
                </>
              ) : (
                `支付 ¥${isSinglePlan ? displayPrice.toFixed(1) : displayPrice}`
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
