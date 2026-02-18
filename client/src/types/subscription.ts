export interface Plan {
  id: string;
  name: string;
  slug: string;
  description?: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  features: string[];
  limits: {
    max_projects?: number;
    max_storage_gb?: number;
    max_members?: number;
  };
  is_active: boolean;
  is_public: boolean;
  created_at: string;
}

export interface Subscription {
  id: string;
  organization_id: string;
  plan_id: string;
  plan: Plan;
  status: 'active' | 'canceled' | 'past_due' | 'unpaid' | 'trialing';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at?: string;
  trial_start?: string;
  trial_end?: string;
  created_at: string;
}

export interface Invoice {
  id: string;
  organization_id: string;
  subscription_id?: string;
  status: 'draft' | 'open' | 'paid' | 'uncollectible' | 'void';
  amount_due: number;
  amount_paid: number;
  currency: string;
  description?: string;
  hosted_invoice_url?: string;
  pdf_url?: string;
  paid_at?: string;
  due_date?: string;
  created_at: string;
}

export interface UsageStatsItem {
  used: number;
  limit: number;
  remaining: number;
  percentage: number;
}

export interface StorageUsageStats {
  used_bytes: number;
  limit_bytes: number;
  remaining_bytes: number;
  percentage: number;
  used_gb: number;
  limit_gb: number;
}

export interface UsageStats {
  projects: UsageStatsItem;
  storage: StorageUsageStats;
  members: UsageStatsItem;
}

export interface PaymentMethod {
  id: string;
  type: string;
  provider: string;
  last4?: string;
  brand?: string;
  exp_month?: number;
  exp_year?: number;
  is_default: boolean;
  created_at: string;
}
