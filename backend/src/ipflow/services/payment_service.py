"""
支付服务
Payment service for handling payment integration

签名验证说明：
- 微信支付 V3：Webhook 使用 ``WECHATPAY2-SHA256-RSA2048``，对 ``timestamp\nnonce\nbody\n`` 用微信平台证书
  RSA 公钥验签。本实现提供 ``verify_wechat_v3_signature``；当未配置平台证书时**拒绝**（安全默认）。
- 支付宝：异步回调使用 ``sign`` + ``sign_type=RSA2``，用支付宝公钥 RSA2048 验签。
  本实现提供 ``verify_alipay_rsa2_signature``；未配置公钥时**拒绝**。

凭证通过 ``settings`` 环境变量加载（``PAYMENT_WECHAT_API_V3_KEY``、``PAYMENT_ALIPAY_PUBLIC_KEY`` 等），
未配置时验签一律返回 ``False``，避免「无签名也放行」的安全漏洞。
"""
import base64
import hashlib
import json
import logging
import os
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


def _settings_get(key: str, default: Optional[str] = None) -> Optional[str]:
    """从环境变量读取支付凭证（隔离对 settings 的耦合）."""
    val = os.environ.get(key)
    return val if val else default


def _skip_signature_verify() -> bool:
    """是否跳过签名验证（仅沙箱/本地仿真环境显式开启）.

    生产环境务必保持 ``PAYMENT_SKIP_SIGNATURE_VERIFY`` 为空或 ``false``。
    """
    val = (os.environ.get("PAYMENT_SKIP_SIGNATURE_VERIFY") or "").lower()
    return val in ("1", "true", "yes", "on")


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

    @staticmethod
    def verify_wechat_v3_signature(
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
        serial: Optional[str] = None,
    ) -> bool:
        """验证微信支付 V3 Webhook 签名.

        待验签串：``timestamp\\nnonce\\nbody\\n``，使用微信平台证书的 RSA 公钥
        （SHA256）验签。平台证书从 ``PAYMENT_WECHAT_PLATFORM_CERT`` 环境变量加载
        （PEM 文本或路径）。

        Args:
            timestamp: HTTP 头 ``Wechatpay-Timestamp``
            nonce: HTTP 头 ``Wechatpay-Nonce``
            body: 原始请求体
            signature: HTTP 头 ``Wechatpay-Signature``（Base64）
            serial: 平台证书序列号（可选，用于多证书场景）

        Returns:
            ``True`` 验签通过；未配置平台证书或验签失败返回 ``False``
        """
        cert_pem = _settings_get("PAYMENT_WECHAT_PLATFORM_CERT")
        if not cert_pem:
            logger.warning("微信支付验签：未配置 PAYMENT_WECHAT_PLATFORM_CERT，拒绝")
            return False
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.exceptions import InvalidSignature

            # 支持文件路径或 PEM 文本
            if cert_pem.strip().startswith("-----"):
                cert_data = cert_pem.encode("utf-8")
            else:
                with open(cert_pem, "rb") as f:
                    cert_data = f.read()
            cert = serialization.load_pem_x509_certificate(cert_data)
            public_key = cert.public_key()

            message = f"{timestamp}\n{nonce}\n{body}\n".encode("utf-8")
            sig_bytes = base64.b64decode(signature)
            try:
                public_key.verify(
                    sig_bytes,
                    message,
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True
            except InvalidSignature:
                logger.warning("微信支付验签：签名不匹配")
                return False
        except Exception as e:  # noqa: BLE001
            logger.error("微信支付验签异常：%s", e)
            return False

    @staticmethod
    def verify_alipay_rsa2_signature(params: dict, sign: str) -> bool:
        """验证支付宝异步回调 RSA2 签名.

        支付宝回调签名是对「除 ``sign``/``sign_type`` 外所有参数按字典序拼接、URL 编码后」
        的字符串进行 RSA-SHA256 验签。支付宝公钥从 ``PAYMENT_ALIPAY_PUBLIC_KEY`` 加载。

        Args:
            params: 回调的全部参数（含 sign/sign_type，函数内部会剔除）
            sign: ``sign`` 参数值（Base64）

        Returns:
            ``True`` 验签通过；未配置公钥或验签失败返回 ``False``
        """
        public_key_pem = _settings_get("PAYMENT_ALIPAY_PUBLIC_KEY")
        if not public_key_pem:
            logger.warning("支付宝验签：未配置 PAYMENT_ALIPAY_PUBLIC_KEY，拒绝")
            return False
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.exceptions import InvalidSignature

            # 公钥可为 PEM 文本或纯 base64 内容
            pem = public_key_pem.strip()
            if not pem.startswith("-----"):
                pem = (
                    "-----BEGIN PUBLIC KEY-----\n"
                    + pem
                    + "\n-----END PUBLIC KEY-----"
                )
            public_key = serialization.load_pem_public_key(pem.encode("utf-8"))

            # 剔除 sign / sign_type，按 key 字典序拼接
            filtered = {
                k: v for k, v in params.items() if k not in ("sign", "sign_type") and v not in (None, "")
            }
            sign_str = "&".join(
                f"{k}={v}" for k, v in sorted(filtered.items())
            )

            sig_bytes = base64.b64decode(sign)
            try:
                public_key.verify(
                    sig_bytes,
                    sign_str.encode("utf-8"),
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True
            except InvalidSignature:
                logger.warning("支付宝验签：签名不匹配")
                return False
        except Exception as e:  # noqa: BLE001
            logger.error("支付宝验签异常：%s", e)
            return False


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
        """验证微信支付回调.

        使用微信支付 V3 平台证书对回调进行 RSA-SHA256 验签。
        未配置平台证书（``PAYMENT_WECHAT_PLATFORM_CERT``）时返回 ``False``，
        避免无签名放行。

        例外：当显式设置 ``PAYMENT_SKIP_SIGNATURE_VERIFY=true``（仅沙箱/仿真）
        时跳过验签直接放行。
        """
        if _skip_signature_verify():
            logger.warning("微信支付 verify_payment：已跳过验签（沙箱模式）")
            return True
        timestamp = data.get("timestamp") or data.get("Wechatpay-Timestamp", "")
        nonce = data.get("nonce") or data.get("Wechatpay-Nonce", "")
        body = data.get("body") or data.get("resource", {}).get("ciphertext", "")
        signature = data.get("signature") or data.get("Wechatpay-Signature", "")
        if not (timestamp and nonce and signature):
            logger.warning("微信支付 verify_payment：缺少验签字段")
            return False
        return self.verify_wechat_v3_signature(
            str(timestamp), str(nonce), body, str(signature)
        )


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
        """验证支付宝异步回调.

        使用支付宝公钥（``PAYMENT_ALIPAY_PUBLIC_KEY``）对 ``sign`` 进行 RSA2 验签。
        未配置公钥或验签失败返回 ``False``，避免无签名放行。

        例外：当显式设置 ``PAYMENT_SKIP_SIGNATURE_VERIFY=true``（仅沙箱/仿真）
        时跳过验签直接放行。
        """
        if _skip_signature_verify():
            logger.warning("支付宝 verify_payment：已跳过验签（沙箱模式）")
            return True
        sign = data.get("sign")
        if not sign:
            logger.warning("支付宝 verify_payment：缺少 sign 字段")
            return False
        return self.verify_alipay_rsa2_signature(data, str(sign))


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
