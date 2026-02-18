"""结构化日志配置."""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from ipflow.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器.
    
    将日志记录格式化为 JSON，便于 ELK/Loki 等日志系统处理。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON.
        
        Args:
            record: 日志记录
            
        Returns:
            JSON 字符串
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加上下文字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "organization_id"):
            log_data["organization_id"] = record.organization_id
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外数据
        if hasattr(record, "extra_data") and record.extra_data:
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """文本格式日志格式化器."""
    
    def __init__(self) -> None:
        """初始化."""
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging() -> None:
    """配置应用日志.
    
    根据环境配置设置日志级别和格式。
    """
    settings = get_settings()
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    
    # 设置格式
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())
    
    root_logger.addHandler(handler)
    
    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # 开发环境增加 SQL 日志
    if settings.is_development:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
