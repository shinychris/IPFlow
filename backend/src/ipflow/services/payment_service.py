"""
支付服务
Payment service for handling payment integration
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
import uuid
import hashlib
import json

logger = logging.getLogger(__name__)


class PaymentService:
    """支付服务基类"""

    def __init__(self):
        self.app_id: Optional[str] = None
        self.app_secret: Optional[str] = None
        self.mch_id: Optional[str] = None  # 商户号
        self.api_key: Optional[str] = None  # API密钥
        self.notify_url: Optional[str] = None

    async def create_payment(
        self,
        user_id: str,
        plan_id: str,
        billing_interval: str,
        payment_method: str,
        amount: int,
        order_no: str,
        client_ip: str,
    ) -> dict:
        """
        创建支付订单

        Args:
            user_id: 用户ID
            plan_id: 计划ID
            billing_interval: 计费周期 (monthly/yearly)
            payment_method: 支付方式 (wechat/alipay)
            amount: 金额（分）
            order_no: 订单号
            client_ip: 客户端IP

        Returns:
            支付订单信息
        """
        raise NotImplementedError

    async def verify_payment(self, payment_id: str, data: dict) -> bool:
        """
        验证支付结果

        Args:
            payment_id: 支付ID
            data: 支付回调数据

        Returns:
            验证是否成功
        """
        raise NotImplementedError

    def generate_order_no(self) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:6].upper()
        return f"IPF{timestamp}{random_str}"

    def generate_sign(self, data: dict, api_key: str) -> str:
        """
        生成签名

        Args:
            data: 待签名数据
            api_key: API密钥

        Returns:
            签名字符串
        """
        # 按key排序
        sorted_data = sorted(data.items())
        # 拼接字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_data if v])
        sign_str += f"&key={api_key}"
        # MD5签名并转大写
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()


class WeChatPayService(PaymentService):
    """微信支付服务（V3版本）"""

    def __init__(self):
        super().__init__()
        # 从环境变量或配置加载
        self.app_id = "your_wechat_app_id"
        self.mch_id = "your_mch_id"
        self.api_key = "your_api_key"
        self.api_v3_key = "your_api_v3_key"
        self.cert_path = "/path/to/cert"
        self.key_path = "/path/to/key"

    async def create_payment(
        self,
        user_id: str,
        plan_id: str,
        billing_interval: str,
        payment_method: str,
        amount: int,
        order_no: str,
        client_ip: str,
    ) -> dict:
        """
        创建微信Native支付（扫码支付）

        返回二维码URL
        """
        import httpx

        # 构建请求参数
        params = {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": f"IPFlow-{plan_id}-{billing_interval}",
            "out_trade_no": order_no,
            "time_expire": (datetime.now() + timedelta(minutes=30)).strftime("%Y%m%d%H%M%S"),
            "notify_url": f"{self.notify_url}/webhook/wechat",
            "amount": {
                "total": amount,
                "currency": "CNY",
            },
            "scene_info": {
                "payer_client_ip": client_ip,
            },
        }

        # TODO: 实际实现需要使用 wechatpayv3 库
        # 这里是模拟实现
        logger.info(f"Creating WeChat payment: {order_no}")

        # 模拟返回二维码URL（实际应该从微信API获取）
        qr_code_url = f"weixin://wxpay/bizpayurl?pr={uuid.uuid4().hex[:16]}"

        return {
            "payment_method": "wechat",
            "qr_code": qr_code_url,
            "order_no": order_no,
            "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat(),
        }

    async def verify_payment(self, payment_id: str, data: dict) -> bool:
        """验证微信支付回调"""
        # TODO: 实现微信支付签名验证
        return True


class AlipayService(PaymentService):
    """支付宝支付服务"""

    def __init__(self):
        super().__init__()
        self.app_id = "your_alipay_app_id"
        self.app_secret = "your_app_secret"
        self.mch_id = "your_mch_id"
        self.private_key_path = "/path/to/private_key"
        self.public_key_path = "/path/to/public_key"

    async def create_payment(
        self,
        user_id: str,
        plan_id: str,
        billing_interval: str,
        payment_method: str,
        amount: int,
        order_no: str,
        client_ip: str,
    ) -> dict:
        """
        创建支付宝网站支付

        返回支付URL
        """
        # 构建请求参数
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.page.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": f"{self.notify_url}/webhook/alipay",
            "biz_content": json.dumps({
                "out_trade_no": order_no,
                "total_amount": str(amount / 100),  # 转换为元
                "subject": f"IPFlow-{plan_id}-{billing_interval}",
                "product_code": "FAST_INSTANT_TRADE_PAY",
            }),
        }

        # 生成签名
        sign = self.generate_sign(params, self.app_secret)
        params["sign"] = sign

        # 构建支付URL
        pay_url = f"https://openapi.alipay.com/gateway.do?{self._build_query(params)}"

        logger.info(f"Creating Alipay payment: {order_no}")

        return {
            "payment_method": "alipay",
            "pay_url": pay_url,
            "order_no": order_no,
            "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat(),
        }

    def _build_query(self, params: dict) -> str:
        """构建查询字符串"""
        return "&".join([f"{k}={v}" for k, v in sorted(params.items())])

    async def verify_payment(self, payment_id: str, data: dict) -> bool:
        """验证支付宝回调"""
        # TODO: 实现支付宝签名验证
        return True


# 支付服务工厂
class PaymentServiceFactory:
    """支付服务工厂"""

    _wechat_service: Optional[WeChatPayService] = None
    _alipay_service: Optional[AlipayService] = None

    @classmethod
    def get_wechat_service(cls) -> WeChatPayService:
        if cls._wechat_service is None:
            cls._wechat_service = WeChatPayService()
        return cls._wechat_service

    @classmethod
    def get_alipay_service(cls) -> AlipayService:
        if cls._alipay_service is None:
            cls._alipay_service = AlipayService()
        return cls._alipay_service

    @classmethod
    def get_service(cls, payment_method: str) -> PaymentService:
        """根据支付方式获取对应的服务"""
        if payment_method == "wechat":
            return cls.get_wechat_service()
        elif payment_method == "alipay":
            return cls.get_alipay_service()
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")
