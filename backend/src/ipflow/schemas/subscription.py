"""订阅与计费Schema.

定义订阅相关的请求和响应模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel


class PlanFeature(BaseModel):
    """计划功能项."""
    name: str
    description: str
    included: bool = True


class PlanResponse(BaseModel):
    """计划响应模型."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    price_monthly: Decimal
    price_yearly: Decimal
    currency: str
    features: List[str]
    limits: Dict[str, Any]
    is_active: bool
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """订阅响应模型."""
    id: UUID
    organization_id: UUID
    plan_id: UUID
    plan: PlanResponse
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    """创建订阅请求."""
    plan_id: UUID
    interval: str = "monthly"  # monthly, yearly
    payment_method_id: Optional[UUID] = None


class SubscriptionUpdate(BaseModel):
    """更新订阅请求."""
    plan_id: Optional[UUID] = None
    cancel_at_period_end: Optional[bool] = None


class InvoiceResponse(BaseModel):
    """发票响应模型."""
    id: UUID
    organization_id: UUID
    subscription_id: Optional[UUID]
    status: str
    amount_due: Decimal
    amount_paid: Decimal
    currency: str
    description: Optional[str]
    hosted_invoice_url: Optional[str]
    pdf_url: Optional[str]
    paid_at: Optional[datetime]
    due_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    """资源使用统计."""
    used: int
    limit: int
    remaining: int
    percentage: float


class StorageUsageStats(BaseModel):
    """存储使用统计."""
    used_bytes: int
    limit_bytes: int
    remaining_bytes: int
    percentage: float
    used_gb: float
    limit_gb: float


class UsageStatsResponse(BaseModel):
    """使用统计响应."""
    projects: UsageStats
    storage: StorageUsageStats
    members: UsageStats


class CheckoutSessionResponse(BaseModel):
    """结账会话响应."""
    session_id: str
    url: str


class PaymentMethodCreate(BaseModel):
    """创建支付方式请求."""
    type: str  # card, alipay, wechat_pay
    provider_token: str
    is_default: bool = False


class PaymentMethodResponse(BaseModel):
    """支付方式响应."""
    id: UUID
    type: str
    provider: str
    last4: Optional[str]
    brand: Optional[str]
    exp_month: Optional[int]
    exp_year: Optional[int]
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
