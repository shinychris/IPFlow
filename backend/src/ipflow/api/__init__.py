"""API 模块.

导出所有 API 路由和版本模块。
"""

from ipflow.api.v1 import api_router

__all__ = ["api_router"]
