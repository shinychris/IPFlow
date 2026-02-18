"""安全模块测试 - TDD (JWT, 密码哈希)."""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext


class TestPasswordHashing:
    """密码哈希测试."""
    
    def test_get_password_hash_returns_string(self):
        """测试密码哈希返回字符串."""
        # Arrange & Act
        from ipflow.core.security import get_password_hash
        hashed = get_password_hash("password123")
        
        # Assert
        assert isinstance(hashed, str)
        assert hashed != "password123"
        assert len(hashed) > 20
    
    def test_verify_password_with_correct_password(self):
        """测试使用正确密码验证通过."""
        # Arrange
        from ipflow.core.security import get_password_hash, verify_password
        hashed = get_password_hash("mypassword")
        
        # Act & Assert
        assert verify_password("mypassword", hashed) is True
    
    def test_verify_password_with_wrong_password(self):
        """测试使用错误密码验证失败."""
        # Arrange
        from ipflow.core.security import get_password_hash, verify_password
        hashed = get_password_hash("mypassword")
        
        # Act & Assert
        assert verify_password("wrongpassword", hashed) is False


class TestJWTToken:
    """JWT 令牌测试."""
    
    @pytest.fixture(autouse=True)
    def setup_config(self, monkeypatch):
        """设置测试配置."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    
    def test_create_access_token_returns_string(self):
        """测试创建访问令牌返回字符串."""
        # Arrange
        from ipflow.core.security import create_access_token
        
        # Act
        token = create_access_token("user-123")
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 50  # JWT 通常较长
        assert token.count(".") == 2  # JWT 有三个部分
    
    def test_create_access_token_contains_correct_data(self):
        """测试访问令牌包含正确数据."""
        # Arrange
        from ipflow.core.security import create_access_token, get_settings
        
        # Act
        token = create_access_token("user-123")
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=["HS256"])
        
        # Assert
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_with_custom_expiry(self):
        """测试自定义过期时间的访问令牌."""
        # Arrange
        from ipflow.core.security import create_access_token, get_settings
        
        # Act
        expires = timedelta(minutes=5)
        token = create_access_token("user-123", expires)
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=["HS256"])
        
        # Assert - 验证过期时间大约在 5 分钟后
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        expiry_duration = exp_timestamp - iat_timestamp
        assert 290 <= expiry_duration <= 310  # 允许一些误差
    
    def test_verify_access_token_valid(self):
        """测试验证有效的访问令牌."""
        # Arrange
        from ipflow.core.security import create_access_token, verify_access_token
        token = create_access_token("user-123")
        
        # Act
        user_id = verify_access_token(token)
        
        # Assert
        assert user_id == "user-123"
    
    def test_verify_access_token_invalid(self):
        """测试验证无效的访问令牌."""
        # Arrange
        from ipflow.core.security import verify_access_token
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid token"):
            verify_access_token("invalid.token.here")
    
    def test_verify_access_token_wrong_type(self):
        """测试验证错误类型的令牌."""
        # Arrange
        from ipflow.core.security import create_refresh_token, verify_access_token
        refresh_token = create_refresh_token("user-123")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid token type"):
            verify_access_token(refresh_token)
    
    def test_verify_access_token_expired(self):
        """测试验证过期的访问令牌."""
        # Arrange
        from ipflow.core.security import get_settings
        import time
        
        # 创建一个已经过期的令牌
        expired_time = datetime.utcnow() - timedelta(minutes=1)
        payload = {
            "sub": "user-123",
            "exp": expired_time,
            "type": "access",
            "iat": expired_time - timedelta(minutes=30),
        }
        expired_token = jwt.encode(payload, get_settings().SECRET_KEY, algorithm="HS256")
        
        # Act & Assert
        from ipflow.core.security import verify_access_token
        with pytest.raises(ValueError, match="Invalid token"):
            verify_access_token(expired_token)


class TestRefreshToken:
    """刷新令牌测试."""
    
    @pytest.fixture(autouse=True)
    def setup_config(self, monkeypatch):
        """设置测试配置."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    
    def test_create_refresh_token_returns_string(self):
        """测试创建刷新令牌返回字符串."""
        # Arrange
        from ipflow.core.security import create_refresh_token
        
        # Act
        token = create_refresh_token("user-123")
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_create_refresh_token_contains_correct_data(self):
        """测试刷新令牌包含正确数据."""
        # Arrange
        from ipflow.core.security import create_refresh_token, get_settings
        
        # Act
        token = create_refresh_token("user-123")
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=["HS256"])
        
        # Assert
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        assert "jti" in payload  # JWT ID
        assert "exp" in payload
    
    def test_verify_refresh_token_valid(self):
        """测试验证有效的刷新令牌."""
        # Arrange
        from ipflow.core.security import create_refresh_token, verify_refresh_token
        token = create_refresh_token("user-123")
        
        # Act
        user_id = verify_refresh_token(token)
        
        # Assert
        assert user_id == "user-123"
    
    def test_verify_refresh_token_wrong_type(self):
        """测试验证错误类型的刷新令牌."""
        # Arrange
        from ipflow.core.security import create_access_token, verify_refresh_token
        access_token = create_access_token("user-123")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid token type"):
            verify_refresh_token(access_token)
