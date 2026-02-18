"""数据库模块.

提供异步数据库连接、会话管理和依赖注入功能。

主要组件:
    - engine: 全局异步数据库引擎
    - AsyncSessionLocal: 异步会话工厂
    - get_db: FastAPI 依赖注入函数

Example:
    ```python
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from ipflow.db import get_db
    
    @app.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
    ```
"""

from ipflow.db.session import (
    AsyncSessionLocal,
    engine,
    get_db,
)

__all__ = [
    "AsyncSessionLocal",
    "engine",
    "get_db",
]
