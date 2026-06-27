"""令牌黑名单服务.

支持登出后令牌立即失效（吊销）。采用「优先 Redis，降级内存」策略：

- **Redis 可用**（生产 / 多实例）：将吊销的令牌 ``jti`` 写入 Redis，TTL 与令牌剩余有效期一致，
  所有实例共享黑名单，登出后立即生效。
- **Redis 不可用**（本地 / 单实例 / 仿真环境）：回退到进程内 ``set``，
  仅对当前进程生效（重启后清空）。

任何对 Redis 的连接异常都会被捕获并降级，绝不影响登录/鉴权主流程。

Redis 键命名：``token:blacklist:{jti}``，值为 ``1``。
"""

import logging
from typing import Optional

from ipflow.config import get_settings

logger = logging.getLogger(__name__)

# 进程内降级黑名单（Redis 不可用时使用）
_in_memory_blacklist: set[str] = set()
# Redis 客户端单例（懒加载）
_redis_client = None
_redis_initialized = False
_redis_available = False


def _get_redis():
    """懒加载 Redis 同步客户端，失败时返回 None 并永久降级到内存。"""
    global _redis_client, _redis_initialized, _redis_available

    if _redis_initialized:
        return _redis_client if _redis_available else None

    _redis_initialized = True
    try:
        import redis  # type: ignore

        settings = get_settings()
        _redis_client = redis.Redis.from_url(
            str(settings.REDIS_URL),
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        # 触发一次 ping 确认可达
        _redis_client.ping()
        _redis_available = True
        logger.info("token_blacklist: Redis 已连接，使用 Redis 共享黑名单")
    except Exception as e:  # noqa: BLE001
        _redis_available = False
        _redis_client = None
        logger.warning(
            "token_blacklist: Redis 不可用（%s），降级到进程内黑名单", e
        )

    return _redis_client if _redis_available else None


def _blacklist_ttl_seconds(exp: int) -> int:
    """根据令牌过期时间戳计算黑名单 TTL（至少 1 秒）。"""
    import time

    remaining = int(exp - time.time())
    return max(remaining, 1)


def revoke_token(jti: str, exp: Optional[int] = None) -> None:
    """吊销令牌（加入黑名单）。

    Args:
        jti: 令牌唯一标识（JWT 的 ``jti`` 声明）
        exp: 令牌过期时间戳（Unix 秒）。提供时用于计算 Redis TTL。
    """
    if not jti:
        return

    client = _get_redis()
    if client is not None:
        try:
            ttl = _blacklist_ttl_seconds(exp) if exp else 3600
            client.setex(f"token:blacklist:{jti}", ttl, "1")
            return
        except Exception as e:  # noqa: BLE001
            logger.warning("token_blacklist: Redis 写入失败，降级到内存：%s", e)

    # 降级：进程内
    _in_memory_blacklist.add(jti)


def is_token_revoked(jti: str) -> bool:
    """检查令牌是否已被吊销。

    Args:
        jti: 令牌唯一标识

    Returns:
        ``True`` 表示已吊销（应拒绝该令牌）
    """
    if not jti:
        return False

    client = _get_redis()
    if client is not None:
        try:
            return bool(client.exists(f"token:blacklist:{jti}"))
        except Exception as e:  # noqa: BLE001
            logger.warning("token_blacklist: Redis 读取失败，降级到内存：%s", e)

    return jti in _in_memory_blacklist


def clear_in_memory_blacklist() -> None:
    """清空进程内黑名单（仅测试用）。"""
    _in_memory_blacklist.clear()
