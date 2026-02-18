import { useEffect } from 'react';
import { 
  Users, 
  Building2, 
  CreditCard, 
  FolderKanban,
  TrendingUp,
  DollarSign 
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminStore } from '@/stores/admin-store';

export default function AdminDashboardPage() {
  const { dashboardStats, isLoading, fetchDashboardStats } = useAdminStore();

  useEffect(() => {
    fetchDashboardStats();
  }, [fetchDashboardStats]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
    }).format(amount);
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">管理后台</h1>
        <p className="text-muted-foreground">系统概览和统计数据</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* 总用户数 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总用户数</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-20" /> : dashboardStats?.total_users}
            </div>
            <p className="text-xs text-muted-foreground">
              本月新增 +{dashboardStats?.new_users_this_month || 0}
            </p>
          </CardContent>
        </Card>

        {/* 组织数 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">组织数</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-20" /> : dashboardStats?.total_organizations}
            </div>
            <p className="text-xs text-muted-foreground">
              活跃订阅 {dashboardStats?.active_subscriptions || 0}
            </p>
          </CardContent>
        </Card>

        {/* 本月收入 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">本月收入</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-20" /> : formatCurrency(dashboardStats?.revenue_this_month || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              来自订阅
            </p>
          </CardContent>
        </Card>

        {/* 项目数 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总项目数</CardTitle>
            <FolderKanban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-20" /> : dashboardStats?.total_projects}
            </div>
            <p className="text-xs text-muted-foreground">
              所有组织
            </p>
          </CardContent>
        </Card>

        {/* 活跃订阅 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活跃订阅</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-20" /> : dashboardStats?.active_subscriptions}
            </div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1" />
              付费用户
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
