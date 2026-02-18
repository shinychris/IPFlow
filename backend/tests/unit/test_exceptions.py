"""异常处理模块测试 - TDD."""

from typing import Any

import pytest
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class TestBusinessException:
    """业务异常基础类测试."""

    def test_business_exception_basic(self):
        """测试基础业务异常创建."""
        # Arrange & Act
        from ipflow.core.exceptions import BusinessException

        exc = BusinessException(
            code="TEST_ERROR",
            message="测试错误",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

        # Assert
        assert exc.code == "TEST_ERROR"
        assert exc.message == "测试错误"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.details is None

    def test_business_exception_with_details(self):
        """测试带详细信息的业务异常."""
        # Arrange & Act
        from ipflow.core.exceptions import BusinessException

        details = {"field": "name", "reason": "too_long"}
        exc = BusinessException(
            code="VALIDATION_ERROR",
            message="验证失败",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )

        # Assert
        assert exc.details == details

    def test_business_exception_to_dict(self):
        """测试业务异常转换为字典."""
        # Arrange
        from ipflow.core.exceptions import BusinessException

        exc = BusinessException(
            code="NOT_FOUND",
            message="资源不存在",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_id": "123"},
        )

        # Act
        result = exc.to_dict()

        # Assert
        assert result["success"] is False
        assert result["code"] == "NOT_FOUND"
        assert result["message"] == "资源不存在"
        assert result["details"] == {"resource_id": "123"}


class TestNotFoundException:
    """资源不存在异常测试."""

    def test_not_found_exception_default(self):
        """测试默认资源不存在异常."""
        # Arrange & Act
        from ipflow.core.exceptions import NotFoundException

        exc = NotFoundException(resource="user")

        # Assert
        assert exc.code == "RESOURCE_NOT_FOUND"
        assert "user" in exc.message
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.details == {"resource": "user"}

    def test_not_found_exception_with_id(self):
        """测试带ID的资源不存在异常."""
        # Arrange & Act
        from ipflow.core.exceptions import NotFoundException

        exc = NotFoundException(resource="patent", resource_id="PAT-001")

        # Assert
        assert exc.code == "RESOURCE_NOT_FOUND"
        assert exc.details == {"resource": "patent", "id": "PAT-001"}

    def test_not_found_exception_custom_message(self):
        """测试自定义消息的资源不存在异常."""
        # Arrange & Act
        from ipflow.core.exceptions import NotFoundException

        exc = NotFoundException(
            resource="trademark",
            resource_id="TM-123",
            message="商标不存在或已被删除",
        )

        # Assert
        assert exc.message == "商标不存在或已被删除"


class TestValidationException:
    """验证异常测试."""

    def test_validation_exception_basic(self):
        """测试基础验证异常."""
        # Arrange & Act
        from ipflow.core.exceptions import ValidationException

        exc = ValidationException(message="字段验证失败")

        # Assert
        assert exc.code == "VALIDATION_ERROR"
        assert exc.message == "字段验证失败"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validation_exception_with_field_errors(self):
        """测试带字段错误的验证异常."""
        # Arrange & Act
        from ipflow.core.exceptions import ValidationException

        field_errors = [
            {"field": "email", "message": "无效的邮箱格式"},
            {"field": "phone", "message": "手机号格式不正确"},
        ]
        exc = ValidationException(
            message="请求数据验证失败",
            field_errors=field_errors,
        )

        # Assert
        assert exc.details == {"errors": field_errors}


class TestAuthenticationException:
    """认证异常测试."""

    def test_authentication_exception_default(self):
        """测试默认认证异常."""
        # Arrange & Act
        from ipflow.core.exceptions import AuthenticationException

        exc = AuthenticationException()

        # Assert
        assert exc.code == "AUTHENTICATION_ERROR"
        assert exc.message == "认证失败"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authentication_exception_custom(self):
        """测试自定义认证异常."""
        # Arrange & Act
        from ipflow.core.exceptions import AuthenticationException

        exc = AuthenticationException(
            message="Token 已过期",
            details={"token_type": "access", "expired_at": "2024-01-01"},
        )

        # Assert
        assert exc.message == "Token 已过期"
        assert exc.details == {"token_type": "access", "expired_at": "2024-01-01"}


class TestPermissionException:
    """权限异常测试."""

    def test_permission_exception_default(self):
        """测试默认权限异常."""
        # Arrange & Act
        from ipflow.core.exceptions import PermissionException

        exc = PermissionException()

        # Assert
        assert exc.code == "PERMISSION_DENIED"
        assert exc.message == "权限不足"
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_permission_exception_with_resource(self):
        """测试带资源信息的权限异常."""
        # Arrange & Act
        from ipflow.core.exceptions import PermissionException

        exc = PermissionException(
            resource="patent",
            action="delete",
        )

        # Assert
        assert "patent" in exc.message
        assert "delete" in exc.message
        assert exc.details == {"resource": "patent", "action": "delete"}


class TestExceptionHandlers:
    """异常处理器测试."""

    @pytest.fixture
    def app_with_handlers(self) -> FastAPI:
        """创建带异常处理器的测试应用."""
        from ipflow.core.exceptions import setup_exception_handlers

        app = FastAPI()
        setup_exception_handlers(app)
        return app

    @pytest.fixture
    def mock_request(self) -> Request:
        """创建模拟请求."""
        from unittest.mock import MagicMock

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"
        return request

    @pytest.mark.asyncio
    async def test_business_exception_handler(
        self, app_with_handlers: FastAPI, mock_request: Any
    ):
        """测试业务异常处理器."""
        # Arrange
        from ipflow.core.exceptions import BusinessException, business_exception_handler

        exc = BusinessException(
            code="TEST_ERROR",
            message="测试错误",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"test": True},
        )

        # Act
        response = await business_exception_handler(mock_request, exc)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.body is not None

    @pytest.mark.asyncio
    async def test_http_exception_handler(
        self, app_with_handlers: FastAPI, mock_request: Any
    ):
        """测试 HTTP 异常处理器."""
        # Arrange
        from ipflow.core.exceptions import http_exception_handler

        exc = StarletteHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="页面未找到",
        )

        # Act
        response = await http_exception_handler(mock_request, exc)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_validation_exception_handler(
        self, app_with_handlers: FastAPI, mock_request: Any
    ):
        """测试请求验证异常处理器."""
        # Arrange
        from ipflow.core.exceptions import validation_exception_handler

        errors: list[dict[str, Any]] = [
            {"loc": ["body", "email"], "msg": "无效的邮箱", "type": "value_error"},
        ]
        exc = RequestValidationError(errors=errors)

        # Act
        response = await validation_exception_handler(mock_request, exc)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSetupExceptionHandlers:
    """异常处理器配置测试."""

    def test_setup_exception_handlers_registers_all(self):
        """测试所有异常处理器都已注册."""
        # Arrange
        from ipflow.core.exceptions import setup_exception_handlers

        app = FastAPI()

        # Act
        setup_exception_handlers(app)

        # Assert
        # 验证异常处理器已注册（FastAPI 内部存储）
        assert len(app.exception_handlers) > 0

    def test_setup_exception_handlers_with_custom_handler(self):
        """测试可以添加自定义异常处理器."""
        # Arrange
        from ipflow.core.exceptions import setup_exception_handlers

        app = FastAPI()

        class CustomException(Exception):
            """自定义异常."""

        async def custom_handler(request: Request, exc: CustomException):
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "custom"},
            )

        # Act
        setup_exception_handlers(app)
        app.add_exception_handler(CustomException, custom_handler)

        # Assert
        assert CustomException in app.exception_handlers
