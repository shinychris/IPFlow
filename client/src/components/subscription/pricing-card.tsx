import { Check, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Plan } from '@/types/subscription';

interface PricingCardProps {
  plan: Plan;
  isCurrentPlan?: boolean;
  interval?: 'monthly' | 'yearly';
  onSelect?: (plan: Plan) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function PricingCard({
  plan,
  isCurrentPlan = false,
  interval = 'monthly',
  onSelect,
  isLoading = false,
  disabled = false,
}: PricingCardProps) {
  const price = interval === 'yearly' ? plan.price_yearly : plan.price_monthly;
  const periodLabel = interval === 'yearly' ? '/年' : '/月';
  
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: plan.currency,
      minimumFractionDigits: 0,
    }).format(price);
  };

  const getPlanBadge = () => {
    switch (plan.slug) {
      case 'enterprise':
        return <Badge className="bg-purple-500">企业版</Badge>;
      case 'pro':
        return <Badge className="bg-blue-500">专业版</Badge>;
      default:
        return <Badge variant="secondary">免费版</Badge>;
    }
  };

  return (
    <Card className={cn(
      "flex flex-col",
      isCurrentPlan && "border-primary ring-2 ring-primary ring-offset-2"
    )}>
      <CardHeader>
        <div className="flex items-center justify-between">
          {getPlanBadge()}
          {isCurrentPlan && (
            <Badge variant="outline" className="text-primary border-primary">
              当前计划
            </Badge>
          )}
        </div>
        <CardTitle className="text-2xl mt-2">{plan.name}</CardTitle>
        <CardDescription>{plan.description}</CardDescription>
      </CardHeader>
      
      <CardContent className="flex-1">
        <div className="mb-6">
          <span className="text-4xl font-bold">{formatPrice(price)}</span>
          <span className="text-muted-foreground">{periodLabel}</span>
        </div>

        {plan.limits && (
          <div className="text-sm text-muted-foreground mb-4 space-y-1">
            {plan.limits.max_projects !== undefined && (
              <p>最多 {plan.limits.max_projects} 个项目</p>
            )}
            {plan.limits.max_storage_gb !== undefined && (
              <p>{plan.limits.max_storage_gb}GB 存储空间</p>
            )}
            {plan.limits.max_members !== undefined && (
              <p>最多 {plan.limits.max_members} 名成员</p>
            )}
          </div>
        )}

        <ul className="space-y-3">
          {plan.features.map((feature, index) => (
            <li key={index} className="flex items-start gap-2">
              <Check className="h-5 w-5 text-primary shrink-0" />
              <span className="text-sm">{feature}</span>
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        <Button
          className="w-full"
          variant={isCurrentPlan ? "outline" : "default"}
          onClick={() => onSelect?.(plan)}
          disabled={disabled || isCurrentPlan || isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              处理中...
            </>
          ) : isCurrentPlan ? (
            '当前计划'
          ) : (
            '选择此计划'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
