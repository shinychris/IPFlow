"""认证 API 集成测试 - TDD.

测试范围:
- POST /auth/register - 用户注册
- POST /auth/login - 用户登录
- POST /auth/logout - 用户登出（预留）
- POST /auth/refresh - 刷新令牌
- GET /auth/me - 获取当前用户
- 输入验证错误
"""

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


# =============================================================================
# Fixtures
# =============================================================================


# Mock AsyncSession for testing
class MockAsyncSession:
    """Mock 数据库会话."""
    
    def __init__(self):
        self.committed = False
        self.closed = False
    
    async def commit(self):
        self.committed = True
    
    async def close(self):
        self.closed = True
    
    async def refresh(self, obj):
        pass
    
    def add(self, obj):
        pass
    
    async def execute(self, *args, **kwargs):
        from sqlalchemy.engine.result import ScalarResult
        return MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()


async def mock_get_db():
    """Mock 数据库依赖."""
    session = MockAsyncSession()
    yield session


def create_test_auth_app() -> FastAPI:
    """创建包含认证路由的测试应用."""
    from fastapi import FastAPI
    from ipflow.core.exceptions import setup_exception_handlers
    from ipflow.api.v1.auth import router as auth_router
    from ipflow.db import get_db
    
    app = FastAPI()
    setup_exception_handlers(app)
    
    # Override database dependency
    app.dependency_overrides[get_db] = mock_get_db
    
    app.include_router(auth_router, prefix="/api/v1")
    return app


@pytest.fixture
def auth_app() -> FastAPI:
    """创建包含认证路由的测试应用."""
    # 每次创建新实例以确保 patch 生效
    return create_test_auth_app()


@pytest.fixture
async def auth_client(auth_app: FastAPI) -> AsyncClient:
    """创建认证测试客户端."""
    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def setup_test_config(monkeypatch):
    """设置测试环境变量."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt-testing")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")


# =============================================================================
# POST /auth/register - 用户注册测试
# =============================================================================


@pytest.mark.asyncio
class TestAuthRegister:
    """用户注册端点测试."""
    
    async def test_register_success(self, auth_client: AsyncClient):
        """测试成功注册用户."""
        # Arrange - Mock 数据库操作
        from ipflow.models.user import User
        
        mock_user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            display_name="Test User",
            is_active=True,
            role="user",
        )
        
        with patch("ipflow.api.v1.auth.get_user_by_email", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.create_user", new=AsyncMock(return_value=mock_user)):
            
            register_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "StrongP@ss123",
                "display_name": "Test User",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/register", json=register_data)
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["email"] == register_data["email"]
            assert data["data"]["username"] == register_data["username"]
            assert "hashed_password" not in data["data"]
            assert "access_token" in data["data"]
            assert data["data"]["token_type"] == "bearer"
    
    async def test_register_without_display_name(self, auth_client: AsyncClient):
        """测试注册时不提供显示名称."""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.display_name = None
        mock_user.status = "active"
        mock_user.role = "user"
        
        with patch("ipflow.api.v1.auth.get_user_by_email", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.create_user", new=AsyncMock(return_value=mock_user)):
            
            register_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "StrongP@ss123",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/register", json=register_data)
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
    
    async def test_register_duplicate_email(self, auth_client: AsyncClient):
        """测试使用已存在的邮箱注册."""
        # Arrange
        from ipflow.models.user import User
        
        existing_user = User(
            id="user-456",
            email="existing@example.com",
            username="existinguser",
            hashed_password="hashed",
        )
        
        with patch("ipflow.api.v1.auth.get_user_by_email", new=AsyncMock(return_value=existing_user)):
            register_data = {
                "email": "existing@example.com",
                "username": "newuser",
                "password": "StrongP@ss123",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/register", json=register_data)
            
            # Assert - ValidationException 返回 422
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert data["success"] is False
            assert data["code"] == "VALIDATION_ERROR"
            assert "email" in data["message"].lower() or "邮箱" in data["message"] or "注册" in data["message"]
    
    async def test_register_duplicate_username(self, auth_client: AsyncClient):
        """测试使用已存在的用户名注册."""
        # Arrange
        from ipflow.models.user import User
        
        existing_user = User(
            id="user-456",
            email="existing@example.com",
            username="existinguser",
            hashed_password="hashed",
        )
        
        with patch("ipflow.api.v1.auth.get_user_by_email", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=existing_user)):
            
            register_data = {
                "email": "new@example.com",
                "username": "existinguser",
                "password": "StrongP@ss123",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/register", json=register_data)
            
            # Assert - ValidationException 返回 422
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert data["success"] is False
            assert data["code"] == "VALIDATION_ERROR"
    
    async def test_register_invalid_email(self, auth_client: AsyncClient):
        """测试使用无效的邮箱格式注册."""
        # Arrange
        register_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "StrongP@ss123",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/register", json=register_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "VALIDATION_ERROR"
    
    async def test_register_short_username(self, auth_client: AsyncClient):
        """测试使用过短的用户名注册."""
        # Arrange
        register_data = {
            "email": "test@example.com",
            "username": "ab",  # 太短
            "password": "StrongP@ss123",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/register", json=register_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_register_short_password(self, auth_client: AsyncClient):
        """测试使用过短的密码注册."""
        # Arrange
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "12345",  # 太短
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/register", json=register_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_register_missing_required_fields(self, auth_client: AsyncClient):
        """测试缺少必填字段."""
        # Arrange - 缺少 password
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/register", json=register_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False


# =============================================================================
# POST /auth/login - 用户登录测试
# =============================================================================


@pytest.mark.asyncio
class TestAuthLogin:
    """用户登录端点测试."""
    
    async def test_login_success(self, auth_client: AsyncClient):
        """测试成功登录."""
        # Arrange
        from ipflow.core.security import get_password_hash
        
        hashed_password = get_password_hash("correctpassword")
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.hashed_password = hashed_password
        mock_user.status = "active"
        mock_user.role = "user"
        mock_user.last_login_at = None
        
        with patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=mock_user)), \
             patch("ipflow.api.v1.auth.get_user_by_email", new=AsyncMock(return_value=None)):
            
            login_data = {
                "username": "testuser",
                "password": "correctpassword",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/login", json=login_data)
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]
            assert data["data"]["token_type"] == "bearer"
            assert data["data"]["username"] == "testuser"
    
    async def test_login_invalid_username(self, auth_client: AsyncClient):
        """测试使用不存在的用户名登录."""
        # Arrange
        with patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.get_user_by_email", new=AsyncMock(return_value=None)):
            
            login_data = {
                "username": "nonexistent",
                "password": "somepassword",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/login", json=login_data)
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["success"] is False
            assert data["code"] == "AUTHENTICATION_ERROR"
    
    async def test_login_invalid_password(self, auth_client: AsyncClient):
        """测试使用错误的密码登录."""
        # Arrange
        from ipflow.core.security import get_password_hash
        
        hashed_password = get_password_hash("correctpassword")
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.username = "testuser"
        mock_user.hashed_password = hashed_password
        mock_user.status = "active"
        
        with patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=mock_user)):
            login_data = {
                "username": "testuser",
                "password": "wrongpassword",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/login", json=login_data)
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["success"] is False
    
    async def test_login_inactive_user(self, auth_client: AsyncClient):
        """测试禁用的用户登录."""
        # Arrange
        from ipflow.core.security import get_password_hash
        
        hashed_password = get_password_hash("correctpassword")
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.username = "testuser"
        mock_user.hashed_password = hashed_password
        mock_user.is_active = False  # 禁用状态
        
        with patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=mock_user)):
            login_data = {
                "username": "testuser",
                "password": "correctpassword",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/login", json=login_data)
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["success"] is False
    
    async def test_login_missing_username(self, auth_client: AsyncClient):
        """测试缺少用户名的请求."""
        # Arrange
        login_data = {
            "password": "somepassword",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_login_missing_password(self, auth_client: AsyncClient):
        """测试缺少密码的请求."""
        # Arrange
        login_data = {
            "username": "testuser",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# POST /auth/refresh - 刷新令牌测试
# =============================================================================


@pytest.mark.asyncio
class TestAuthRefresh:
    """令牌刷新端点测试."""
    
    async def test_refresh_success(self, auth_client: AsyncClient):
        """测试成功刷新令牌."""
        # Arrange
        from ipflow.core.security import create_refresh_token
        
        user_id = "user-123"
        refresh_token = create_refresh_token(user_id)
        
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.username = "testuser"
        mock_user.status = "active"
        
        with patch("ipflow.api.v1.auth.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            refresh_data = {
                "refresh_token": refresh_token,
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
            assert data["data"]["token_type"] == "bearer"
            assert "expires_in" in data["data"]
    
    async def test_refresh_invalid_token(self, auth_client: AsyncClient):
        """测试使用无效的刷新令牌."""
        # Arrange
        refresh_data = {
            "refresh_token": "invalid.token.here",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "AUTHENTICATION_ERROR"
    
    async def test_refresh_access_token_instead_of_refresh(self, auth_client: AsyncClient):
        """测试错误地使用访问令牌作为刷新令牌."""
        # Arrange
        from ipflow.core.security import create_access_token
        
        access_token = create_access_token("user-123")
        
        refresh_data = {
            "refresh_token": access_token,
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_refresh_user_not_found(self, auth_client: AsyncClient):
        """测试刷新令牌但用户不存在."""
        # Arrange
        from ipflow.core.security import create_refresh_token
        
        refresh_token = create_refresh_token("nonexistent-user")
        
        with patch("ipflow.api.v1.auth.get_user_by_id", new=AsyncMock(return_value=None)):
            refresh_data = {
                "refresh_token": refresh_token,
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_refresh_inactive_user(self, auth_client: AsyncClient):
        """测试刷新禁用用户的令牌."""
        # Arrange
        from ipflow.core.security import create_refresh_token
        
        user_id = "user-123"
        refresh_token = create_refresh_token(user_id)
        
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.username = "testuser"
        mock_user.is_active = False  # 禁用
        
        with patch("ipflow.api.v1.auth.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            refresh_data = {
                "refresh_token": refresh_token,
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_refresh_missing_token(self, auth_client: AsyncClient):
        """测试缺少刷新令牌."""
        # Arrange
        refresh_data = {}
        
        # Act
        response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# POST /auth/logout - 用户登出测试（预留）
# =============================================================================


@pytest.mark.asyncio
class TestAuthLogout:
    """用户登出端点测试（功能预留）."""
    
    async def test_logout_with_token(self, auth_client: AsyncClient):
        """测试携带令牌登出."""
        # Arrange
        from ipflow.core.security import create_access_token
        from ipflow.models.user import User, UserRole, UserStatus
        from uuid import uuid4
        
        user_id = str(uuid4())
        access_token = create_access_token(user_id)
        
        mock_user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role=UserRole.MEMBER,
            status=UserStatus.ACTIVE,
        )
        
        with patch("ipflow.api.v1.auth.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            # Act
            response = await auth_client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK


# =============================================================================
# GET /auth/me - 获取当前用户测试
# =============================================================================


@pytest.mark.asyncio
class TestAuthMe:
    """获取当前用户端点测试."""
    
    async def test_get_me_success(self, auth_client: AsyncClient):
        """测试成功获取当前用户信息."""
        # Arrange
        from ipflow.core.security import create_access_token
        from uuid import uuid4
        
        user_id = str(uuid4())
        access_token = create_access_token(user_id)
        
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.display_name = "Test User"
        mock_user.role = "member"
        mock_user.status = "active"
        mock_user.created_at = datetime.utcnow()
        mock_user.updated_at = datetime.utcnow()
        mock_user.last_login_at = None
        
        with patch("ipflow.api.v1.auth.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            # Act
            response = await auth_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == user_id
            assert data["data"]["email"] == "test@example.com"
            assert data["data"]["username"] == "testuser"
            assert "hashed_password" not in data["data"]
    
    async def test_get_me_no_token(self, auth_client: AsyncClient):
        """测试未提供令牌."""
        # Act
        response = await auth_client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
    
    async def test_get_me_invalid_token(self, auth_client: AsyncClient):
        """测试无效的令牌."""
        # Act
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_me_expired_token(self, auth_client: AsyncClient):
        """测试过期的令牌."""
        # Arrange - 创建一个过期的令牌
        from jose import jwt
        from ipflow.config import get_settings
        
        settings = get_settings()
        expired_time = datetime.utcnow() - timedelta(minutes=1)
        payload = {
            "sub": "user-123",
            "exp": expired_time,
            "type": "access",
            "iat": expired_time - timedelta(minutes=30),
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        # Act
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_me_user_not_found(self, auth_client: AsyncClient):
        """测试令牌有效但用户不存在."""
        # Arrange
        from ipflow.core.security import create_access_token
        
        access_token = create_access_token("nonexistent-user")
        
        with patch("ipflow.api.v1.auth.get_user_by_id", new=AsyncMock(return_value=None)):
            # Act
            response = await auth_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_get_me_inactive_user(self, auth_client: AsyncClient):
        """测试获取禁用用户的信息."""
        # Arrange
        from ipflow.core.security import create_access_token
        
        user_id = "user-123"
        access_token = create_access_token(user_id)
        
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.username = "testuser"
        mock_user.is_active = False
        
        with patch("ipflow.api.v1.auth.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            # Act
            response = await auth_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_me_malformed_auth_header(self, auth_client: AsyncClient):
        """测试格式错误的认证头."""
        # Act
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat token"},
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# 输入验证错误测试
# =============================================================================


@pytest.mark.asyncio
class TestAuthValidation:
    """认证 API 输入验证测试."""
    
    async def test_register_email_too_long(self, auth_client: AsyncClient):
        """测试邮箱过长."""
        # Arrange
        register_data = {
            "email": "a" * 250 + "@example.com",  # 太长
            "username": "testuser",
            "password": "StrongP@ss123",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/register", json=register_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_register_username_with_special_chars(self, auth_client: AsyncClient):
        """测试用户名包含特殊字符."""
        # Arrange
        register_data = {
            "email": "test@example.com",
            "username": "test@user!",  # 特殊字符
            "password": "StrongP@ss123",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/register", json=register_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_register_username_too_long(self, auth_client: AsyncClient):
        """测试用户名过长."""
        # Arrange
        register_data = {
            "email": "test@example.com",
            "username": "a" * 51,  # 超过最大长度 50
            "password": "StrongP@ss123",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/register", json=register_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_login_empty_username(self, auth_client: AsyncClient):
        """测试空用户名."""
        # Arrange
        login_data = {
            "username": "",
            "password": "password123",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_login_empty_password(self, auth_client: AsyncClient):
        """测试空密码."""
        # Arrange
        login_data = {
            "username": "testuser",
            "password": "",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_refresh_empty_token(self, auth_client: AsyncClient):
        """测试空刷新令牌."""
        # Arrange
        refresh_data = {
            "refresh_token": "",
        }
        
        # Act
        response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# 响应格式测试
# =============================================================================


@pytest.mark.asyncio
class TestAuthResponseFormat:
    """认证 API 响应格式测试."""
    
    async def test_success_response_format(self, auth_client: AsyncClient):
        """测试成功响应格式."""
        # Arrange
        from ipflow.models.user import User
        
        mock_user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            display_name="Test User",
            is_active=True,
            role="user",
        )
        
        with patch("ipflow.api.v1.auth.get_user_by_email", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=None)), \
             patch("ipflow.api.v1.auth.create_user", new=AsyncMock(return_value=mock_user)):
            
            register_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "StrongP@ss123",
            }
            
            # Act
            response = await auth_client.post("/api/v1/auth/register", json=register_data)
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "success" in data
            assert "code" in data
            assert "message" in data
            assert "data" in data
            assert data["success"] is True
            assert data["code"] == "SUCCESS"
    
    async def test_error_response_format(self, auth_client: AsyncClient):
        """测试错误响应格式."""
        # Act - 发送无效数据触发验证错误
        response = await auth_client.post("/api/v1/auth/register", json={})
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "success" in data
        assert "code" in data
        assert "message" in data
        assert "details" in data
        assert data["success"] is False
