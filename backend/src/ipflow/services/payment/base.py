"""支付提供商基类.

定义支付服务接口。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID


class PaymentCustomer:
    """支付客户数据类."""
    
    def __init__(
        self,
        id: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.email = email
        self.name = name
        self.metadata = metadata or {}


class PaymentSubscription:
    """支付订阅数据类."""
    
    def __init__(
        self,
        id: str,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        cancel_at_period_end: bool = False,
        canceled_at: Optional[datetime] = None,
        trial_start: Optional[datetime] = None,
        trial_end: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.status = status
        self.current_period_start = current_period_start
        self.current_period_end = current_period_end
        self.cancel_at_period_end = cancel_at_period_end
        self.canceled_at = canceled_at
        self.trial_start = trial_start
        self.trial_end = trial_end
        self.metadata = metadata or {}


class PaymentInvoice:
    """支付发票数据类."""
    
    def __init__(
        self,
        id: str,
        status: str,
        amount_due: Decimal,
        currency: str,
        hosted_invoice_url: Optional[str] = None,
        pdf_url: Optional[str] = None,
        paid_at: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.status = status
        self.amount_due = amount_due
        self.currency = currency
        self.hosted_invoice_url = hosted_invoice_url
        self.pdf_url = pdf_url
        self.paid_at = paid_at
        self.due_date = due_date
        self.description = description
        self.metadata = metadata or {}


class PaymentIntent:
    """支付意图数据类."""
    
    def __init__(
        self,
        id: str,
        client_secret: str,
        status: str,
        amount: Decimal,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.client_secret = client_secret
        self.status = status
        self.amount = amount
        self.currency = currency
        self.metadata = metadata or {}


class BasePaymentProvider(ABC):
    """支付提供商基类.
    
    所有支付提供商（Stripe、支付宝、微信支付）都需要实现此接口。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称."""
        pass
    
    # === 客户管理 ===
    
    @abstractmethod
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentCustomer:
        """创建客户."""
        pass
    
    @abstractmethod
    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentCustomer:
        """更新客户."""
        pass
    
    @abstractmethod
    async def delete_customer(self, customer_id: str) -> bool:
        """删除客户."""
        pass
    
    # === 订阅管理 ===
    
    @abstractmethod
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        trial_days: int = 0,
    ) -> PaymentSubscription:
        """创建订阅."""
        pass
    
    @abstractmethod
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> PaymentSubscription:
        """取消订阅."""
        pass
    
    @abstractmethod
    async def update_subscription(
        self,
        subscription_id: str,
        price_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentSubscription:
        """更新订阅."""
        pass
    
    @abstractmethod
    async def get_subscription(self, subscription_id: str) -> Optional[PaymentSubscription]:
        """获取订阅详情."""
        pass
    
    # === 发票管理 ===
    
    @abstractmethod
    async def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> List[PaymentInvoice]:
        """列出客户发票."""
        pass
    
    @abstractmethod
    async def get_invoice(self, invoice_id: str) -> Optional[PaymentInvoice]:
        """获取发票详情."""
        pass
    
    # === 支付管理 ===
    
    @abstractmethod
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentIntent:
        """创建支付意图."""
        pass
    
    @abstractmethod
    async def confirm_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """确认支付意图."""
        pass
    
    # === Webhook处理 ===
    
    @abstractmethod
    async def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """验证Webhook签名."""
        pass
    
    @abstractmethod
    async def parse_webhook_event(self, payload: str) -> Dict[str, Any]:
        """解析Webhook事件."""
        pass
