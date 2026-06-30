"""异常处理模块.

提供统一的业务异常类和 FastAPI 异常处理器。
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class BusinessException(Exception):
    """业务异常基类.

    所有业务相关异常都应继承此类，提供统一的错误响应格式。

    Attributes:
        code: 错误代码，用于客户端识别错误类型
        message: 错误消息，用于显示给用户
        status_code: HTTP 状态码
        details: 额外的错误详情
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化业务异常.

        Args:
            code: 错误代码
            message: 错误消息
            status_code: HTTP 状态码
            details: 额外的错误详情
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        """将异常转换为字典格式.

        Returns:
            统一格式的错误响应字典
        """
        return {
            "success": False,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundException(BusinessException):
    """资源不存在异常.

    当请求的资源不存在时抛出。

    Examples:
        >>> raise NotFoundException(resource="user", resource_id="123")
        >>> raise NotFoundException(resource="patent", message="专利不存在")
    """

    def __init__(
        self,
        resource: str = "resource",
        resource_id: str | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化资源不存在异常.

        Args:
            resource: 资源类型名称
            resource_id: 资源标识
            message: 自定义错误消息
            details: 额外的错误详情
        """
        # 构建默认消息
        if message is None:
            if resource_id:
                message = f"{resource} 不存在 (ID: {resource_id})"
            else:
                message = f"{resource} 不存在"

        # 构建详情
        error_details: dict[str, Any] = {"resource": resource}
        if resource_id:
            error_details["id"] = resource_id
        if details:
            error_details.update(details)

        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details,
        )


class ValidationException(BusinessException):
    """数据验证异常.

    当请求数据验证失败时抛出。

    Examples:
        >>> raise ValidationException(message="字段验证失败")
        >>> raise ValidationException(
        ...     message="请求数据验证失败",
        ...     field_errors=[{"field": "email", "message": "无效的邮箱格式"}]
        ... )
    """

    def __init__(
        self,
        message: str = "请求数据验证失败",
        field_errors: list[dict[str, Any]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化验证异常.

        Args:
            message: 错误消息
            field_errors: 字段级别的错误列表
            details: 额外的错误详情
        """
        error_details: dict[str, Any] = details or {}
        if field_errors:
            error_details["errors"] = field_errors

        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=error_details or None,
        )


class ConflictException(BusinessException):
    """资源冲突异常.

    当请求与已存在的资源冲突时抛出（如邮箱/用户名已注册、唯一约束冲突等）。
    区别于 ``ValidationException``（422，请求数据本身不合法），本异常表示数据合法但
    与现有资源冲突，语义对应 HTTP 409 Conflict。

    Examples:
        >>> raise ConflictException(message="该邮箱已被注册")
        >>> raise ConflictException(
        ...     message="该邮箱已被注册",
        ...     field_errors=[{"field": "email", "message": "邮箱已被使用"}]
        ... )
    """

    def __init__(
        self,
        message: str = "资源已存在",
        field_errors: list[dict[str, Any]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化冲突异常.

        Args:
            message: 错误消息
            field_errors: 字段级别的错误列表
            details: 额外的错误详情
        """
        error_details: dict[str, Any] = details or {}
        if field_errors:
            error_details["errors"] = field_errors

        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=error_details or None,
        )


class AuthenticationException(BusinessException):
    """认证异常.

    当用户认证失败时抛出（如 Token 无效、已过期等）。

    Examples:
        >>> raise AuthenticationException()
        >>> raise AuthenticationException(message="Token 已过期")
    """

    def __init__(
        self,
        message: str = "认证失败",
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化认证异常.

        Args:
            message: 错误消息
            details: 额外的错误详情
        """
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class PermissionException(BusinessException):
    """权限异常.

    当用户没有权限执行某个操作时抛出。

    Examples:
        >>> raise PermissionException()
        >>> raise PermissionException(resource="patent", action="delete")
    """

    def __init__(
        self,
        resource: str | None = None,
        action: str | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化权限异常.

        Args:
            resource: 被访问的资源类型
            action: 尝试执行的操作
            message: 自定义错误消息
            details: 额外的错误详情
        """
        # 构建默认消息
        if message is None:
            if resource and action:
                message = f"没有权限 {action} 该 {resource}"
            else:
                message = "权限不足"

        # 构建详情
        error_details: dict[str, Any] = details or {}
        if resource:
            error_details["resource"] = resource
        if action:
            error_details["action"] = action

        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=error_details or None,
        )


# ==================== 异常处理器 ====================


async def business_exception_handler(
    request: Request,
    exc: BusinessException,
) -> JSONResponse:
    """处理业务异常.

    Args:
        request: FastAPI 请求对象
        exc: 业务异常实例

    Returns:
        JSON 响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """处理 Starlette HTTP 异常.

    Args:
        request: FastAPI 请求对象
        exc: HTTP 异常实例

    Returns:
        JSON 响应
    """
    # 将 HTTPException 转换为统一格式
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "details": None,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """处理请求验证异常.

    Args:
        request: FastAPI 请求对象
        exc: 请求验证异常实例

    Returns:
        JSON 响应
    """
    # 格式化验证错误
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        error_detail: dict[str, Any] = {
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        errors.append(error_detail)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "code": "VALIDATION_ERROR",
            "message": "请求数据验证失败",
            "details": {"errors": errors},
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """处理通用异常（捕获未处理的异常）.

    所有未处理的 500 错误都会上报到监控（Sentry）+ 告警 Webhook，
    避免线上错误静默丢失。

    Args:
        request: FastAPI 请求对象
        exc: 异常实例

    Returns:
        JSON 响应
    """
    # 上报到监控（Sentry 可选）+ 推送告警
    import logging
    from ipflow.core.alerting import capture_exception, send_alert

    logger = logging.getLogger(__name__)
    logger.exception("未处理异常：%s", exc)

    capture_exception(
        exc,
        path=str(request.url.path),
        method=request.method,
    )

    # 异步推送告警（不阻塞响应；错误收集后由事件循环调度）
    import asyncio
    asyncio.create_task(
        send_alert(
            title="服务端未处理异常",
            detail=f"{request.method} {request.url.path}\n{type(exc).__name__}: {exc}",
            level="error",
        )
    )

    # 生产环境不暴露详细的异常信息
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "details": None,
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """配置 FastAPI 应用的异常处理器.

    Args:
        app: FastAPI 应用实例

    Examples:
        >>> from fastapi import FastAPI
        >>> from ipflow.core.exceptions import setup_exception_handlers
        >>> app = FastAPI()
        >>> setup_exception_handlers(app)
    """
    # 注册业务异常处理器
    app.add_exception_handler(BusinessException, business_exception_handler)

    # 注册 HTTP 异常处理器
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # 注册验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # 注册通用异常处理器（捕获所有未处理的异常）
    app.add_exception_handler(Exception, generic_exception_handler)
