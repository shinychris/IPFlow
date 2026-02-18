"""数据库会话管理模块.

提供异步数据库引擎、会话工厂和依赖注入功能。
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ipflow.config import get_settings

# 私有实例变量
_engine_instance: AsyncEngine | None = None
_session_factory_instance: async_sessionmaker[AsyncSession] | None = None


def _create_engine() -> AsyncEngine:
    """创建异步数据库引擎.
    
    Returns:
        AsyncEngine: 配置好的异步数据库引擎
    """
    settings = get_settings()
    database_url = str(settings.DATABASE_URL)

    return create_async_engine(
        database_url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG,  # 仅在调试模式下输出 SQL
    )


def _create_session_factory() -> async_sessionmaker[AsyncSession]:
    """创建异步会话工厂.
    
    Returns:
        async_sessionmaker: 配置好的异步会话工厂
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = _create_engine()
    return async_sessionmaker(
        _engine_instance,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def __getattr__(name: str) -> Any:
    """模块级别的延迟加载.
    
    在首次访问 engine 或 AsyncSessionLocal 时才创建实例。
    
    Args:
        name: 属性名
        
    Returns:
        请求的属性值
        
    Raises:
        AttributeError: 如果属性不存在
    """
    global _engine_instance, _session_factory_instance

    if name == "engine":
        if _engine_instance is None:
            _engine_instance = _create_engine()
        return _engine_instance

    if name == "AsyncSessionLocal":
        if _session_factory_instance is None:
            _session_factory_instance = _create_session_factory()
        return _session_factory_instance

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """返回模块公开的属性列表."""
    return ["engine", "AsyncSessionLocal", "get_db"]


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """获取数据库会话依赖.
    
    用于 FastAPI 依赖注入，提供异步数据库会话。
    会话会在请求结束后自动关闭。
    
    Yields:
        AsyncSession: 异步数据库会话
    
    Example:
        ```python
        from fastapi import Depends
        from ipflow.db import get_db
        
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
        ```
    """
    # 导入时可能还没有 AsyncSessionLocal，通过 __getattr__ 获取
    from ipflow.db import session

    session_factory = session.AsyncSessionLocal
    async with session_factory() as db_session:
        try:
            yield db_session
        finally:
            await db_session.close()
