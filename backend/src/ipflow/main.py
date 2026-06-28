"""FastAPI 应用入口."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ipflow.config import get_settings
from ipflow.core.exceptions import setup_exception_handlers
from ipflow.core.logging import setup_logging
from ipflow.core.middleware import RequestLoggingMiddleware
from ipflow.core.monitoring import health_checker
from ipflow.db.session import get_db

settings = get_settings()

# 配置日志
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    # 启动时
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.APP_NAME} v2.0.0")
    
    # 创建数据库表（开发环境）
    if settings.is_development:
        await create_tables()
        # 初始化尼斯分类基础数据（商标模块开箱可用）
        try:
            from ipflow.db import AsyncSessionLocal
            from ipflow.db.nice_seed import seed_nice_classifications

            async with AsyncSessionLocal() as session:
                added = await seed_nice_classifications(session)
                if added:
                    logger.info(f"已初始化 {added} 个尼斯分类")
        except Exception as e:  # noqa: BLE001 初始化失败不应阻断启动
            logger.warning(f"尼斯分类初始化失败（可忽略）：{e}")

    yield
    
    # 关闭时
    logger.info(f"Shutting down {settings.APP_NAME}")


async def create_tables():
    """创建数据库表（仅开发环境使用）."""
    from sqlmodel import SQLModel
    from ipflow.db import engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="知识产权申请管理平台 API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 配置异常处理器
setup_exception_handlers(app)

# 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from ipflow.api.v1 import api_router as v1_router
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查端点."""
    # 获取数据库会话
    from ipflow.db import async_session_maker
    
    async with async_session_maker() as db:
        health_status = await health_checker.check_all(db)
    
    return {
        "status": health_status["status"],
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": health_status["timestamp"],
        "checks": health_status["checks"],
    }


@app.get("/health/simple")
async def simple_health_check():
    """简单健康检查（仅返回状态）."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """根路径."""
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT,
    }


def main():
    """CLI 入口."""
    import uvicorn
    uvicorn.run(
        "ipflow.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
