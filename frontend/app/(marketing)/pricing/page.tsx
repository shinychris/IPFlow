"use client";

/**
 * 定价页面
 * Pricing page - display subscription plans and handle plan selection
 */
import { PricingCalculator } from "@/components/marketing/pricing-calculator";
import { PricingCards } from "@/components/marketing/pricing-cards";
import { PlanComparison } from "@/components/marketing/plan-comparison";
import { FAQSection } from "@/components/marketing/faq-section";
import { PaymentModal } from "@/components/payment/payment-modal";
import { usePaymentStore } from "@/stores/payment-store";

export default function PricingPage() {
  const { openPayment } = usePaymentStore();

  const handlePlanSelect = (planId: string) => {
    // 企业版和代理版跳转到联系销售
    if (planId === "enterprise" || planId === "agency") {
      window.location.href = "/contact?plan=" + planId;
      return;
    }

    // 其他计划打开支付弹窗
    openPayment(planId);
  };

  return (
    <div className="flex flex-col">
      {/* Page Header */}
      <section className="py-16 bg-muted/30">
        <div className="container text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            选择适合您的计划
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            无免费版，新增按次付费（¥19.0/次）。未通过可联系客服退款。
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16">
        <div className="container">
          <PricingCards
            billingInterval="yearly"
            onPlanSelect={handlePlanSelect}
          />
        </div>
      </section>

      {/* Pricing Calculator */}
      <section className="py-16 bg-muted/30">
        <div className="container max-w-4xl">
          <PricingCalculator />
        </div>
      </section>

      {/* Plan Comparison */}
      <section className="py-16">
        <div className="container">
          <PlanComparison />
        </div>
      </section>

      {/* FAQ */}
      <FAQSection />

      {/* Payment Modal */}
      <PaymentModal />
    </div>
  );
}
