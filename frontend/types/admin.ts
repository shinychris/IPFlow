export interface DashboardStats {
  total_users: number;
  new_users_this_month: number;
  total_organizations: number;
  active_subscriptions: number;
  revenue_this_month: number;
  total_projects: number;
}

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  display_name?: string;
  role: 'super_admin' | 'admin' | 'manager' | 'member' | 'viewer';
  status: 'active' | 'inactive' | 'suspended';
  email_verified: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface AdminOrganization {
  id: string;
  name: string;
  slug: string;
  plan_type: string;
  max_projects: number;
  max_storage_bytes: number;
  max_members: number;
  used_storage_bytes: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  member_count?: number;
}

export interface AdminPlan {
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
  updated_at: string;
}

export interface AdminAuditLog {
  id: string;
  user_id?: string;
  organization_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  description?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}
