import { useEffect, useState } from 'react';
import { CreditCard, Receipt, BarChart3, AlertCircle } from 'lucide-react';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';

import { useSubscriptionStore } from '@/stores/subscription-store';
import { PricingCard } from '@/components/subscription/pricing-card';
import { UsageStatsCard } from '@/components/subscription/usage-stats';
import { InvoiceList } from '@/components/subscription/invoice-list';
import type { Plan } from '@/types/subscription';

export default function SubscriptionPage() {
  const [interval, setInterval] = useState<'monthly' | 'yearly'>('monthly');
  const [isUpgrading, setIsUpgrading] = useState(false);
  
  const {
    plans,
    currentSubscription,
    invoices,
    usageStats,
    isLoading,
    error,
    fetchPlans,
    fetchCurrentSubscription,
    fetchInvoices,
    fetchUsageStats,
    createSubscription,
    cancelSubscription,
    clearError,
  } = useSubscriptionStore();

  useEffect(() => {
    fetchPlans();
    fetchCurrentSubscription();
    fetchInvoices();
    fetchUsageStats();
  }, [fetchPlans, fetchCurrentSubscription, fetchInvoices, fetchUsageStats]);

  const handleSelectPlan = async (plan: Plan) => {
    if (currentSubscription) {
      // 升级/降级
      setIsUpgrading(true);
      try {
        // 这里应该调用升级API
        // await updateSubscription({ planId: plan.id });
      } finally {
        setIsUpgrading(false);
      }
    } else {
      // 新建订阅
      setIsUpgrading(true);
      try {
        await createSubscription(plan.id, interval);
      } finally {
        setIsUpgrading(false);
      }
    }
  };

  const handleCancelSubscription = async () => {
    if (confirm('确定要取消订阅吗？您仍可以使用服务直到当前周期结束。')) {
      await cancelSubscription(true);
    }
  };

  if (isLoading && plans.length === 0) {
    return (
      <div className="container py-10 max-w-6xl">
        <Skeleton className="h-10 w-64 mb-6" />
        <div className="grid gap-6 md:grid-cols-3">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  return (
    <div className="container py-10 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">订阅与计费</h1>
          <p className="text-muted-foreground">
            管理您的订阅计划和使用情况
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>错误</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="plans" className="space-y-6">
        <TabsList>
          <TabsTrigger value="plans">
            <CreditCard className="mr-2 h-4 w-4" />
            订阅计划
          </TabsTrigger>
          <TabsTrigger value="usage">
            <BarChart3 className="mr-2 h-4 w-4" />
            使用情况
          </TabsTrigger>
          <TabsTrigger value="invoices">
            <Receipt className="mr-2 h-4 w-4" />
            发票记录
          </TabsTrigger>
        </TabsList>

        <TabsContent value="plans" className="space-y-6">
          {currentSubscription && (
            <Card>
              <CardHeader>
                <CardTitle>当前订阅</CardTitle>
                <CardDescription>
                  您的订阅状态和使用期限
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{currentSubscription.plan.name}</p>
                    <p className="text-sm text-muted-foreground">
                      状态: {currentSubscription.status === 'active' ? '活跃' : currentSubscription.status}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      周期结束: {new Date(currentSubscription.current_period_end).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                  {currentSubscription.cancel_at_period_end ? (
                    <Alert className="w-auto">
                      <AlertTitle>订阅将在周期结束后取消</AlertTitle>
                    </Alert>
                  ) : (
                    <Button 
                      variant="outline" 
                      onClick={handleCancelSubscription}
                    >
                      取消订阅
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-center mb-6">
            <div className="inline-flex rounded-lg border p-1">
              <Button
                variant={interval === 'monthly' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setInterval('monthly')}
              >
                月付
              </Button>
              <Button
                variant={interval === 'yearly' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setInterval('yearly')}
              >
                年付
                <span className="ml-2 text-xs bg-green-500 text-white px-2 py-0.5 rounded">
                  省20%
                </span>
              </Button>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {plans.map((plan) => (
              <PricingCard
                key={plan.id}
                plan={plan}
                interval={interval}
                isCurrentPlan={currentSubscription?.plan_id === plan.id}
                onSelect={handleSelectPlan}
                isLoading={isUpgrading}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="usage">
          {usageStats ? (
            <UsageStatsCard stats={usageStats} />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              加载使用统计中...
            </div>
          )}
        </TabsContent>

        <TabsContent value="invoices">
          <Card>
            <CardHeader>
              <CardTitle>发票记录</CardTitle>
              <CardDescription>
                查看和下载您的历史发票
              </CardDescription>
            </CardHeader>
            <CardContent>
              <InvoiceList invoices={invoices} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
