"""邮箱验证与密码重置的令牌服务.

基于 JWT 签发短时效、带用途（``purpose``）的令牌，避免引入额外存储。
令牌通过邮件链接回传到前端，前端调用对应验证端点完成操作。

用途类型：
- ``email_verification``：邮箱验证（注册后发送，有效期 24h）
- ``password_reset``：密码重置（忘记密码时发送，有效期 1h）

安全要点：
- 令牌绑定 ``user_id`` + ``purpose``，验证时三者必须匹配
- ``purpose`` 不符的令牌不可互用（防邮箱验证令牌被用于重置密码）
- 令牌有时效，过期需重新申请
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from ipflow.config import get_settings

logger = logging.getLogger(__name__)

# 用途常量
PURPOSE_EMAIL_VERIFICATION = "email_verification"
PURPOSE_PASSWORD_RESET = "password_reset"

# 各用途的有效期
_TTL: dict[str, timedelta] = {
    PURPOSE_EMAIL_VERIFICATION: timedelta(hours=24),
    PURPOSE_PASSWORD_RESET: timedelta(hours=1),
}


@dataclass
class TokenPayload:
    """解析后的令牌载荷."""

    user_id: str
    purpose: str
    is_valid: bool
    error: Optional[str] = None


def create_action_token(user_id: str, purpose: str) -> str:
    """签发带用途的动作令牌.

    Args:
        user_id: 用户ID
        purpose: 用途（email_verification / password_reset）

    Returns:
        JWT 令牌字符串
    """
    settings = get_settings()
    ttl = _TTL.get(purpose, timedelta(hours=1))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "purpose": purpose,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_action_token(token: str, expected_purpose: str) -> TokenPayload:
    """验证动作令牌.

    Args:
        token: JWT 令牌字符串
        expected_purpose: 期望的用途（必须与令牌内 purpose 一致）

    Returns:
        ``TokenPayload``，``is_valid=False`` 时 ``error`` 说明原因
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        return TokenPayload(user_id="", purpose="", is_valid=False, error="令牌已过期，请重新申请")
    except jwt.PyJWTError:
        return TokenPayload(user_id="", purpose="", is_valid=False, error="无效的令牌")

    user_id = payload.get("sub")
    purpose = payload.get("purpose")
    if not user_id or not purpose:
        return TokenPayload(user_id="", purpose="", is_valid=False, error="令牌载荷不完整")
    if purpose != expected_purpose:
        return TokenPayload(
            user_id=user_id, purpose=purpose, is_valid=False,
            error="令牌用途不匹配",
        )
    return TokenPayload(user_id=user_id, purpose=purpose, is_valid=True)
