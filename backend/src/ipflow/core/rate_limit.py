"""速率限制（基于 slowapi）.

用于防止暴力破解登录、批量注册、AI 接口刷量等。限流器基于内存计数（默认），
生产环境可通过 ``REDIS_URL`` 切换到 Redis 存储以支持多实例。

限流策略（按 IP）：
- 登录：5 次/分钟
- 注册：3 次/小时
- 密码重置请求：3 次/小时
- AI 草稿生成：10 次/分钟
- 文件上传：20 次/分钟
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from ipflow.config import get_settings


def _build_storage_uri() -> str:
    """构建限流存储 URI（优先 Redis，未配置则内存）.

    仅在环境变量 ``REDIS_URL`` 被显式设置时启用 Redis 存储，
    以区分「用户真实部署配置」与「pydantic 默认值」——
    避免开发/测试环境因默认 Redis 地址导致限流器初始化连接失败。
    """
    import os

    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        return redis_url
    return "memory://"


# 限流器单例（按客户端 IP 计数）
limiter = Limiter(key_func=get_remote_address, storage_uri=_build_storage_uri())
