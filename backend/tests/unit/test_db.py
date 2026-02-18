"""数据库模块测试 - TDD."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class TestDatabaseEngine:
    """数据库引擎测试类."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """设置测试环境变量."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    def test_engine_creation(self):
        """测试异步数据库引擎创建."""
        # Arrange & Act
        from ipflow.db.session import engine

        # Assert
        assert engine is not None
        assert isinstance(engine, AsyncEngine)

    def test_engine_uses_correct_url(self, monkeypatch):
        """测试引擎使用正确的数据库 URL."""
        # Arrange
        test_url = "postgresql+asyncpg://testuser:testpass@dbhost:5432/mydb"
        monkeypatch.setenv("DATABASE_URL", test_url)

        # 清除缓存，强制重新创建引擎
        from ipflow.config import get_settings
        from ipflow.db import session as db_session_module

        get_settings.cache_clear()
        # 重置引擎实例
        db_session_module._engine_instance = None

        with patch("ipflow.db.session.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine

            # Act - 访问引擎触发创建
            _ = db_session_module.__getattr__("engine")

            # Assert
            mock_create_engine.assert_called_once()
            call_args = mock_create_engine.call_args
            assert str(call_args[0][0]) == test_url

    def test_engine_pool_configuration(self):
        """测试连接池配置."""
        # Arrange
        from ipflow.config import get_settings

        settings = get_settings()

        # 重置引擎实例以强制重新创建
        from ipflow.db import session as db_session_module

        db_session_module._engine_instance = None

        # Act & Assert
        with patch("ipflow.db.session.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine

            # 访问引擎触发创建
            _ = db_session_module.__getattr__("engine")

            # Check pool configuration
            call_kwargs = mock_create_engine.call_args[1]
            assert call_kwargs.get("pool_size") == settings.DATABASE_POOL_SIZE
            assert call_kwargs.get("max_overflow") == settings.DATABASE_MAX_OVERFLOW
            assert call_kwargs.get("pool_pre_ping") is True
            assert call_kwargs.get("echo") is settings.DEBUG


class TestAsyncSessionLocal:
    """AsyncSessionLocal 测试类."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """设置测试环境变量."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    def test_async_session_local_exists(self):
        """测试 AsyncSessionLocal 存在且类型正确."""
        # Arrange & Act
        from ipflow.db.session import AsyncSessionLocal

        # Assert
        assert AsyncSessionLocal is not None
        assert isinstance(AsyncSessionLocal, async_sessionmaker)

    def test_async_session_local_configuration(self):
        """测试 AsyncSessionLocal 配置."""
        # Arrange & Act
        from ipflow.db.session import AsyncSessionLocal

        # Assert
        # async_sessionmaker 应该配置正确
        assert AsyncSessionLocal.kw.get("expire_on_commit") is False
        assert "bind" in AsyncSessionLocal.kw


class TestGetDB:
    """get_db 依赖注入函数测试类."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """设置测试环境变量."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """测试 get_db 产生异步会话."""
        # Arrange
        from ipflow.db.session import get_db

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("ipflow.db.session.AsyncSessionLocal", mock_session_factory):
            # Act
            async_gen = get_db()
            session = await async_gen.__anext__()

            # Assert
            assert session is mock_session
            mock_session_factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_closes_session(self):
        """测试 get_db 正确关闭会话."""
        # Arrange
        from ipflow.db.session import get_db

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("ipflow.db.session.AsyncSessionLocal", mock_session_factory):
            # Act
            async_gen = get_db()
            await async_gen.__anext__()

            # Simulate end of context (should close session via __aexit__)
            try:
                await async_gen.__anext__()
            except StopAsyncIteration:
                pass

            # Assert - 会话通过上下文管理器关闭
            mock_session_factory.return_value.__aexit__.assert_called()

    @pytest.mark.asyncio
    async def test_get_db_context_manager_behavior(self):
        """测试 get_db 作为上下文管理器的行为."""
        # Arrange
        from ipflow.db.session import get_db

        mock_session = AsyncMock(spec=AsyncSession)
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory = MagicMock(return_value=mock_context_manager)

        with patch("ipflow.db.session.AsyncSessionLocal", mock_session_factory):
            # Act - 手动消费 async generator 来模拟 FastAPI 依赖行为
            async_gen = get_db()
            session = await async_gen.__anext__()

            # Assert - 验证获取到会话
            assert session is mock_session

            # 关闭生成器，触发清理
            try:
                await async_gen.__anext__()
            except StopAsyncIteration:
                pass

            # 验证上下文管理器退出
            mock_context_manager.__aexit__.assert_called()


class TestDBModuleExports:
    """DB 模块导出测试类."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """设置测试环境变量."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    def test_module_exports_engine(self):
        """测试模块导出 engine."""
        # Arrange & Act
        from ipflow.db import engine

        # Assert
        assert engine is not None

    def test_module_exports_async_session_local(self):
        """测试模块导出 AsyncSessionLocal."""
        # Arrange & Act
        from ipflow.db import AsyncSessionLocal

        # Assert
        assert AsyncSessionLocal is not None

    def test_module_exports_get_db(self):
        """测试模块导出 get_db."""
        # Arrange & Act
        from ipflow.db import get_db

        # Assert
        assert callable(get_db)
