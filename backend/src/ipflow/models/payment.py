"""
支付数据模型
Payment data models
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field
from enum import Enum


class PaymentStatus(str, Enum):
    """支付状态"""
    PENDING = "pending"          # 待支付
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
    REFUNDED = "refunded"        # 已退款


class PaymentMethod(str, Enum):
    """支付方式"""
    WECHAT = "wechat"
    ALIPAY = "alipay"
    STRIPE = "stripe"


class BillingInterval(str, Enum):
    """计费周期"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


# 支付订单表
class PaymentOrder(SQLModel, table=True):
    """支付订单"""
    __tablename__ = "payment_orders"

    id: Optional[str] = Field(default=None, primary_key=True)
    order_no: str = Field(unique=True, index=True, max_length=64)
    user_id: UUID = Field(foreign_key="user.id", index=True)

    # 订单信息
    plan_id: str = Field(max_length=50)
    plan_name: str = Field(max_length=100)
    billing_interval: BillingInterval = Field(default=BillingInterval.YEARLY)

    # 支付信息
    payment_method: PaymentMethod = Field(default=PaymentMethod.WECHAT)
    amount: int = Field(default=0)  # 金额（分）
    currency: str = Field(default="CNY", max_length=10)

    # 状态
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)

    # 第三方支付信息
    transaction_id: Optional[str] = Field(default=None, max_length=128)  # 第三方交易号
    qr_code: Optional[str] = Field(default=None)  # 微信支付二维码URL
    pay_url: Optional[str] = Field(default=None)  # 支付宝跳转URL

    # 时间
    expires_at: datetime = Field(default=None)  # 订单过期时间
    paid_at: Optional[datetime] = Field(default=None)  # 支付时间
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 元数据 (使用 extra_data 避免与 SQLAlchemy 的 metadata 保留字冲突)
    extra_data: Optional[str] = Field(
        default=None, 
        sa_column=Column("metadata", String, nullable=True)
    )  # JSON格式的额外信息


# 支付回调日志表
class PaymentWebhookLog(SQLModel, table=True):
    """支付回调日志"""
    __tablename__ = "payment_webhook_logs"

    id: Optional[str] = Field(default=None, primary_key=True)
    payment_id: Optional[str] = Field(default=None, foreign_key="payment_orders.id", index=True)
    order_no: Optional[str] = Field(default=None, max_length=64, index=True)
    event_id: str = Field(index=True, unique=True, max_length=128)

    # 回调信息
    provider: str = Field(max_length=20)  # wechat, alipay
    payload: str = Field(default="")  # 回调数据（JSON）

    # 处理结果
    success: bool = Field(default=False)
    error_message: Optional[str] = Field(default=None)

    # 时间
    created_at: datetime = Field(default_factory=datetime.now)


# 发票表
class Invoice(SQLModel, table=True):
    """发票"""
    __tablename__ = "invoices"

    id: Optional[str] = Field(default=None, primary_key=True)
    payment_id: str = Field(foreign_key="payment_orders.id", index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)

    # 发票信息
    invoice_no: str = Field(unique=True, index=True, max_length=64)
    type: str = Field(default="electronic", max_length=20)  # electronic, paper
    title: str = Field(max_length=200)  # 发票抬头

    # 金额
    amount: int = Field(default=0)  # 金额（分）

    # 状态
    status: str = Field(default="pending", max_length=20)  # pending, issued, cancelled

    # 发票URL（PDF）
    pdf_url: Optional[str] = Field(default=None)

    # 时间
    issued_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


# Pydantic 模型（API）
class PaymentOrderCreate(SQLModel):
    """创建支付订单"""
    plan_id: str = Field(alias="planId")
    billing_interval: BillingInterval = Field(alias="billingInterval")
    payment_method: PaymentMethod = Field(alias="paymentMethod")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }


class PaymentOrderResponse(SQLModel):
    """支付订单响应"""
    id: str
    order_no: str
    amount: int
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    qr_code: Optional[str] = None
    pay_url: Optional[str] = None
    expires_at: datetime

    plan: dict  # {id, name}


class PaymentStatusResponse(SQLModel):
    """支付状态响应"""
    order_id: str
    status: PaymentStatus
    paid_at: Optional[datetime] = None
