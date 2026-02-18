"""配置管理测试 - TDD."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError


class TestSettings:
    """配置设置测试类."""
    
    def test_settings_loads_from_env(self, monkeypatch):
        """测试从环境变量加载配置."""
        # Arrange
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Act
        from ipflow.config import Settings
        settings = Settings()
        
        # Assert
        assert settings.SECRET_KEY == "test-secret-key"
        assert "localhost" in str(settings.DATABASE_URL)
        assert settings.REDIS_URL.host == "localhost"
    
    def test_settings_raises_without_required_vars(self, monkeypatch):
        """测试缺少必需环境变量时抛出异常."""
        # Arrange - 确保没有 SECRET_KEY
        monkeypatch.delenv("SECRET_KEY", raising=False)
        
        # Act & Assert
        from ipflow.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        
        assert "SECRET_KEY" in str(exc_info.value)
    
    def test_default_values(self, monkeypatch):
        """测试默认值."""
        # Arrange
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Act
        from ipflow.config import Settings
        settings = Settings()
        
        # Assert
        assert settings.APP_NAME == "IPFlow"
        assert settings.DEBUG is False
        assert settings.ENVIRONMENT == "development"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.ALGORITHM == "HS256"
    
    def test_get_settings_returns_singleton(self, monkeypatch):
        """测试 get_settings 返回单例."""
        # Arrange
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Act
        from ipflow.config import get_settings
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Assert
        assert settings1 is settings2
    
    def test_database_url_parsing(self, monkeypatch):
        """测试数据库 URL 解析."""
        # Arrange
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@db:5432/ipflow")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Act
        from ipflow.config import Settings
        settings = Settings()
        
        # Assert - 验证 URL 字符串包含预期内容
        url_str = str(settings.DATABASE_URL)
        assert "postgres" in url_str
        assert "password" in url_str
        assert "db" in url_str
        assert "5432" in url_str
