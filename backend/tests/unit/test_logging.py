"""日志模块测试 - TDD."""

import json
import logging
from io import StringIO

import pytest
import structlog


class TestJSONFormatter:
    """JSON 格式化器测试."""
    
    def test_json_formatter_outputs_valid_json(self):
        """测试 JSON 格式化器输出有效 JSON."""
        # Arrange
        from ipflow.core.logging import JSONFormatter
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        # Act
        output = formatter.format(record)
        
        # Assert
        parsed = json.loads(output)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert "timestamp" in parsed
    
    def test_json_formatter_includes_extra_fields(self):
        """测试包含额外字段."""
        # Arrange
        from ipflow.core.logging import JSONFormatter
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-123"
        record.user_id = "user-456"
        
        # Act
        output = formatter.format(record)
        
        # Assert
        parsed = json.loads(output)
        assert parsed["request_id"] == "req-123"
        assert parsed["user_id"] == "user-456"
    
    def test_json_formatter_handles_exception(self):
        """测试处理异常信息."""
        # Arrange
        from ipflow.core.logging import JSONFormatter
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error",
                args=(),
                exc_info=exc_info,
            )
        
        # Act
        output = formatter.format(record)
        
        # Assert
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestSetupLogging:
    """日志设置测试."""
    
    def test_setup_logging_configures_root_logger(self, monkeypatch):
        """测试配置根日志记录器."""
        # Arrange - 设置环境变量并清除缓存
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("LOG_FORMAT", "json")
        
        # 清除 settings 缓存
        from ipflow.config import get_settings
        get_settings.cache_clear()
        
        # Act
        from ipflow.core.logging import setup_logging
        from ipflow.config import get_settings
        
        # 清除之前的设置
        logging.getLogger().handlers.clear()
        
        setup_logging()
        
        # Assert
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
        assert root_logger.level == logging.DEBUG
