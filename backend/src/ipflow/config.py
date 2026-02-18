"""配置管理 - Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import PostgresDsn, RedisDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类.
    
    从环境变量加载配置，支持 .env 文件。
    必需环境变量: SECRET_KEY, DATABASE_URL, REDIS_URL
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    # 应用配置
    APP_NAME: str = Field(default="IPFlow", description="应用名称")
    DEBUG: bool = Field(default=False, description="调试模式")
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    
    # 安全配置
    SECRET_KEY: str = Field(description="JWT 密钥")
    ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        description="访问令牌过期时间(分钟)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, 
        description="刷新令牌过期时间(天)"
    )
    
    # 数据库配置
    DATABASE_URL: PostgresDsn = Field(description="数据库连接 URL")
    DATABASE_POOL_SIZE: int = Field(default=10, description="连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="连接池溢出")
    
    # Redis 配置
    REDIS_URL: RedisDsn = Field(description="Redis 连接 URL")
    
    # 存储配置
    STORAGE_TYPE: str = Field(default="minio", description="存储类型")
    STORAGE_ENDPOINT: str = Field(default="localhost:9000", description="存储端点")
    STORAGE_ACCESS_KEY: str = Field(default="", description="存储访问密钥")
    STORAGE_SECRET_KEY: str = Field(default="", description="存储秘密密钥")
    STORAGE_BUCKET: str = Field(default="ipflow", description="存储桶名称")
    STORAGE_REGION: str = Field(default="us-east-1", description="存储区域")
    STORAGE_USE_SSL: bool = Field(default=False, description="使用 SSL")
    
    # Celery 配置
    CELERY_BROKER_URL: Optional[str] = Field(default=None, description="Celery Broker")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None, description="Celery 结果后端")
    
    # 邮件配置
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP 主机")
    SMTP_PORT: int = Field(default=587, description="SMTP 端口")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP 用户")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP 密码")
    SMTP_TLS: bool = Field(default=True, description="SMTP TLS")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(default="json", description="日志格式")
    
    # 功能开关
    ENABLE_REGISTRATION: bool = Field(default=True, description="启用注册")
    ENABLE_AI_ASSISTANT: bool = Field(default=False, description="启用 AI 助手")
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境."""
        return self.ENVIRONMENT == "production"
    
    @property
    def sync_database_url(self) -> str:
        """获取同步数据库 URL (用于 alembic)."""
        return str(self.DATABASE_URL).replace(
            "postgresql+asyncpg://", 
            "postgresql://"
        )


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例.
    
    Returns:
        Settings: 应用配置实例
    """
    return Settings()
