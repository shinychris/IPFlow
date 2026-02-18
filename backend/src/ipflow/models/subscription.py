"""订阅与计费模型.

定义订阅计划、订阅记录和发票模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey, Text, JSON
from sqlmodel import Field, SQLModel


class PlanInterval(str, Enum):
    """计费周期."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    """订阅状态."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class InvoiceStatus(str, Enum):
    """发票状态."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    UNCOLLECTIBLE = "uncollectible"
    VOID = "void"


class Plan(SQLModel, table=True):
    """订阅计划模型.
    
    Attributes:
        id: 计划唯一标识
        name: 计划名称
        slug: 计划标识
        description: 计划描述
        price_monthly: 月付价格
        price_yearly: 年付价格
        currency: 货币代码
        features: 功能列表
        limits: 资源限制
        is_active: 是否可用
        is_public: 是否公开
        created_at: 创建时间
    """
    
    __tablename__ = "plan"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String(100), nullable=False))
    slug: str = Field(sa_column=Column(String(50), unique=True, nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    # 价格
    price_monthly: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    price_yearly: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    currency: str = Field(default="CNY", sa_column=Column(String(3), nullable=False))
    
    # 功能与限制
    features: List[str] = Field(default=[], sa_column=Column(JSON, default=list))
    limits: dict = Field(default={}, sa_column=Column(JSON, default=dict))
    # limits 示例: {"max_projects": 10, "max_storage_gb": 1, "max_members": 5}
    
    # 状态
    is_active: bool = Field(default=True, sa_column=Column(Boolean, default=True))
    is_public: bool = Field(default=True, sa_column=Column(Boolean, default=True))
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))


class Subscription(SQLModel, table=True):
    """订阅记录模型.
    
    Attributes:
        id: 订阅唯一标识
        organization_id: 组织ID
        plan_id: 计划ID
        status: 订阅状态
        current_period_start: 当前周期开始
        current_period_end: 当前周期结束
        cancel_at_period_end: 是否到期取消
        canceled_at: 取消时间
        trial_start: 试用期开始
        trial_end: 试用期结束
        payment_provider: 支付提供商
        payment_provider_subscription_id: 外部订阅ID
        created_at: 创建时间
    """
    
    __tablename__ = "subscription"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(sa_column=Column(ForeignKey("organization.id"), nullable=False, index=True))
    plan_id: UUID = Field(sa_column=Column(ForeignKey("plan.id"), nullable=False))
    
    # 状态
    status: SubscriptionStatus = Field(
        default=SubscriptionStatus.ACTIVE,
        sa_column=Column(String(20), nullable=False)
    )
    
    # 周期
    current_period_start: datetime = Field(sa_column=Column(DateTime, nullable=False))
    current_period_end: datetime = Field(sa_column=Column(DateTime, nullable=False))
    cancel_at_period_end: bool = Field(default=False, sa_column=Column(Boolean, default=False))
    canceled_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    
    # 试用
    trial_start: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    trial_end: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    
    # 支付提供商
    payment_provider: Optional[str] = Field(default=None, sa_column=Column(String(50), nullable=True))
    payment_provider_subscription_id: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))


class Invoice(SQLModel, table=True):
    """发票记录模型.
    
    Attributes:
        id: 发票唯一标识
        organization_id: 组织ID
        subscription_id: 订阅ID
        status: 发票状态
        amount_due: 应付金额
        amount_paid: 已付金额
        currency: 货币
        description: 描述
        hosted_invoice_url: 发票URL
        pdf_url: PDF URL
        paid_at: 支付时间
        created_at: 创建时间
    """
    
    __tablename__ = "invoice"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(sa_column=Column(ForeignKey("organization.id"), nullable=False, index=True))
    subscription_id: Optional[UUID] = Field(default=None, sa_column=Column(ForeignKey("subscription.id"), nullable=True))
    
    # 状态与金额
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT, sa_column=Column(String(20), nullable=False))
    amount_due: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    amount_paid: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2), default=Decimal("0.00")))
    currency: str = Field(default="CNY", sa_column=Column(String(3), nullable=False))
    
    # 详情
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    lines: List[dict] = Field(default=[], sa_column=Column(JSON, default=list))
    
    # 支付提供商
    payment_provider: Optional[str] = Field(default=None, sa_column=Column(String(50), nullable=True))
    payment_provider_invoice_id: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    hosted_invoice_url: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    pdf_url: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    
    # 时间
    paid_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    due_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))


class PaymentMethod(SQLModel, table=True):
    """支付方式模型.
    
    Attributes:
        id: 支付方式唯一标识
        organization_id: 组织ID
        type: 支付方式类型
        provider: 支付提供商
        provider_payment_method_id: 外部支付方式ID
        last4: 卡号后四位
        brand: 卡品牌
        exp_month: 过期月
        exp_year: 过期年
        is_default: 是否默认
        created_at: 创建时间
    """
    
    __tablename__ = "payment_method"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(sa_column=Column(ForeignKey("organization.id"), nullable=False, index=True))
    
    # 支付方式信息
    type: str = Field(sa_column=Column(String(50), nullable=False))  # card, alipay, wechat_pay
    provider: str = Field(sa_column=Column(String(50), nullable=False))  # stripe, alipay, wechat
    provider_payment_method_id: str = Field(sa_column=Column(String(255), nullable=False))
    
    # 卡信息（如果是卡支付）
    last4: Optional[str] = Field(default=None, sa_column=Column(String(4), nullable=True))
    brand: Optional[str] = Field(default=None, sa_column=Column(String(50), nullable=True))
    exp_month: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    exp_year: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    
    # 状态
    is_default: bool = Field(default=False, sa_column=Column(Boolean, default=False))
    
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
