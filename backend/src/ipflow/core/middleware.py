"""中间件模块.

提供审计日志、请求追踪等中间件。
"""

import time
import uuid
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件.
    
    记录请求处理时间和基本信息。
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # 设置请求ID
        request.state.request_id = request_id
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # 记录日志（可选）
        # logger.info(
        #     f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
        # )
        
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件.
    
    自动记录关键操作的审计日志。
    """
    
    # 需要记录的操作
    AUDIT_PATHS = {
        "POST": ["/api/v1/projects", "/api/v1/organizations"],
        "PUT": ["/api/v1/projects", "/api/v1/organizations"],
        "PATCH": ["/api/v1/projects", "/api/v1/organizations"],
        "DELETE": ["/api/v1/projects", "/api/v1/organizations", "/api/v1/users"],
    }
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否需要记录审计日志
        should_audit = self._should_audit(request)
        
        if should_audit:
            # 记录旧值（如果是更新操作）
            old_values = None
            
        # 继续处理请求
        response = await call_next(request)
        
        # 记录审计日志
        if should_audit and response.status_code < 400:
            await self._log_audit(request, response)
        
        return response
    
    def _should_audit(self, request: Request) -> bool:
        """检查是否应该记录审计日志."""
        method = request.method
        path = request.url.path
        
        if method not in self.AUDIT_PATHS:
            return False
        
        for audit_path in self.AUDIT_PATHS[method]:
            if path.startswith(audit_path):
                return True
        
        return False
    
    async def _log_audit(self, request: Request, response: Response):
        """记录审计日志."""
        # 这里可以实现异步记录审计日志
        # 例如发送到消息队列或直接写入数据库
        pass


class CORSMiddleware:
    """CORS中间件配置."""
    
    @staticmethod
    def get_cors_config(allow_origins=None):
        """获取CORS配置."""
        from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
        
        return {
            "middleware_class": FastAPICORSMiddleware,
            "allow_origins": allow_origins or ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
