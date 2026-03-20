/**
 * 营销页面类型定义
 * Marketing page type definitions
 */

// 客户证言
export interface Testimonial {
  id: string;
  name: string;
  role: string;
  company: string;
  avatar?: string;
  content: string;
  rating: number;
  projectType: "copyright" | "patent" | "trademark";
  certificateImage?: string;
  createdAt: string;
}

// 客户案例
export interface CaseStudy {
  id: string;
  company: string;
  companyLogo?: string;
  industry: string;
  challenge: string;
  solution: string;
  results: {
    label: string;
    value: string;
  }[];
  projectType: "copyright" | "patent" | "trademark";
  testimonial: string;
  certificateImages: string[];
}

// 营销统计数据
export interface MarketingStats {
  totalUsers: number;
  totalProjects: number;
  successRate: number;
  avgProcessTime: number;
  projectsByType: {
    copyright: number;
    patent: number;
    trademark: number;
  };
}

// 定价计划
export interface PricingPlan {
  id: string;
  name: string;
  slug: string;
  price: {
    monthly: number;
    yearly: number;
  };
  description: string;
  badge?: string;
  badgeColor?: string;
  features: string[];
  limits: {
    maxProjects: number;
    maxStorageGb: number;
    maxMembers: number;
  };
  ctaText: string;
  highlighted: boolean;
}

// 定价功能对比
export interface PricingFeature {
  id: string;
  name: string;
  description?: string;
  category: string;
  plans: {
    single: boolean | string;
    starter: boolean | string;
    professional: boolean | string;
    enterprise: boolean | string;
    agency: boolean | string;
  };
}

// 利润测算器状态
export interface CalculatorState {
  projectCount: number;
  billingInterval: "monthly" | "yearly";
  currentMethod: "agency" | "manual" | "other";
  agencyFee: number;
}

// 利润测算器结果
export interface CalculatorResult {
  traditionalCost: number;
  ipflowCost: number;
  savings: number;
  savingsPercentage: number;
  timeSaved: number;
  timeSavedUnit: string;
}

// 流程步骤
export interface ProcessStep {
  step: number;
  title: string;
  description: string;
  icon: string;
  estimatedTime: string;
}

// 导航项
export interface NavItem {
  label: string;
  href: string;
  description?: string;
}

// CTA按钮
export interface CTAButton {
  text: string;
  subtext?: string;
  href: string;
  variant: "primary" | "secondary" | "outline" | "ghost";
  icon: string;
}

// 统计数据项
export interface StatItem {
  value: string;
  label: string;
  trend?: "up" | "down";
  description?: string;
}
