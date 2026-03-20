/**
 * IPFlow 首页 - 营销落地页
 * IPFlow homepage - marketing landing page
 */
import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";
import { HeroSection } from "@/components/marketing/hero-section";
import { StatsBanner } from "@/components/marketing/stats-banner";
import { ProcessSteps } from "@/components/marketing/process-steps";
import { FeatureCards } from "@/components/marketing/feature-cards";
import { TestimonialCarousel } from "@/components/marketing/testimonial-carousel";
import { CTASection } from "@/components/marketing/cta-section";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <HeroSection />
        <StatsBanner />
        <ProcessSteps />
        <FeatureCards />
        <TestimonialCarousel />
        <CTASection />
      </main>
      <SiteFooter />
    </div>
  );
}
