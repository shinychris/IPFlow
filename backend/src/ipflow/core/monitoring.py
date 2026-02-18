"""监控与告警模块.

提供系统健康检查和监控指标。
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthChecker:
    """健康检查器."""
    
    def __init__(self):
        self.checks: Dict[str, callable] = {}
    
    def register(self, name: str, check_func: callable):
        """注册健康检查."""
        self.checks[name] = check_func
    
    async def check_all(self, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """执行所有健康检查."""
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func(db) if db else await check_func()
                results["checks"][name] = {"status": "healthy", **result}
            except Exception as e:
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                results["status"] = "unhealthy"
        
        return results


# 全局健康检查器
health_checker = HealthChecker()


async def check_database(db: AsyncSession) -> Dict[str, Any]:
    """检查数据库连接."""
    start_time = time.time()
    result = await db.execute(text("SELECT 1"))
    result.scalar()
    response_time = time.time() - start_time
    
    return {
        "response_time_ms": round(response_time * 1000, 2),
    }


async def check_redis() -> Dict[str, Any]:
    """检查Redis连接."""
    # 这里实现Redis健康检查
    return {"status": "ok"}


async def check_storage() -> Dict[str, Any]:
    """检查存储服务."""
    # 这里实现MinIO健康检查
    return {"status": "ok"}


# 注册默认检查
health_checker.register("database", check_database)
health_checker.register("redis", check_redis)
health_checker.register("storage", check_storage)


class MetricsCollector:
    """指标收集器.
    
    收集系统运行指标。
    """
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "requests_total": 0,
            "requests_by_path": {},
            "errors_total": 0,
            "errors_by_type": {},
            "response_time_sum": 0.0,
            "response_time_count": 0,
        }
    
    def record_request(self, path: str, status_code: int, response_time: float):
        """记录请求指标."""
        self.metrics["requests_total"] += 1
        self.metrics["requests_by_path"][path] = self.metrics["requests_by_path"].get(path, 0) + 1
        self.metrics["response_time_sum"] += response_time
        self.metrics["response_time_count"] += 1
        
        if status_code >= 400:
            self.metrics["errors_total"] += 1
            error_type = f"{status_code // 100}xx"
            self.metrics["errors_by_type"][error_type] = self.metrics["errors_by_type"].get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标."""
        avg_response_time = 0.0
        if self.metrics["response_time_count"] > 0:
            avg_response_time = self.metrics["response_time_sum"] / self.metrics["response_time_count"]
        
        return {
            "requests_total": self.metrics["requests_total"],
            "errors_total": self.metrics["errors_total"],
            "error_rate": self.metrics["errors_total"] / max(self.metrics["requests_total"], 1),
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_by_path": self.metrics["requests_by_path"],
            "errors_by_type": self.metrics["errors_by_type"],
        }


# 全局指标收集器
metrics_collector = MetricsCollector()
