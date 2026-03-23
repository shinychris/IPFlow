"""配置管理 - Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import PostgresDsn, RedisDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# 计算 .env 文件路径（相对于本文件）
# 本文件在 backend/src/ipflow/config.py，.env 在 backend/.env
_ENV_FILE_PATH = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    """应用配置类.
    
    从环境变量加载配置，支持 .env 文件。
    必需环境变量: SECRET_KEY, DATABASE_URL, REDIS_URL
    """
    
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_PATH,
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
    
    # AI/LLM 配置
    AI_PROVIDER: str = Field(default="ollama", description="AI 提供商: ollama, openai, anthropic")
    AI_MODEL: str = Field(default="llama3.2", description="默认 AI 模型名称")
    
    # Ollama 配置
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama 服务地址")
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama3.2", description="Ollama 默认模型")
    OLLAMA_TIMEOUT: int = Field(default=120, description="Ollama 请求超时(秒)")
    
    # OpenAI 配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, description="OpenAI 基础 URL")
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI 默认模型")
    
    # Anthropic 配置
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API Key")
    ANTHROPIC_DEFAULT_MODEL: str = Field(default="claude-3-haiku-20240307", description="Anthropic 默认模型")

    # 软著草稿生成：template（模板）或 claude_code（Claude Code CLI）
    COPYRIGHT_DRAFT_BACKEND: str = Field(
        default="template",
        description="软著 AI 草稿后端: template, claude_code",
    )
    COPYRIGHT_DRAFT_FALLBACK_TO_TEMPLATE: bool = Field(
        default=False,
        description="Claude Code 失败时是否回退到模板（默认关闭）",
    )
    CLAUDE_CODE_BIN: str = Field(default="claude", description="Claude Code CLI 可执行文件")
    CLAUDE_CODE_SKILL_PROMPT_FILE: str = Field(
        default="resources/skills/software-copyright-application/SKILL.md",
        description="软著技能系统提示文件（相对 backend 根目录或绝对路径）",
    )
    CLAUDE_CODE_TIMEOUT_SECONDS: int = Field(default=600, description="Claude Code 子进程超时(秒)")
    CLAUDE_CODE_MAX_TURNS: int = Field(default=32, description="Claude Code max-turns（若 CLI 支持）")
    CLAUDE_CODE_BARE_MODE: bool = Field(
        default=True,
        description="使用 --bare 减少对本机 ~/.claude 的依赖",
    )
    CLAUDE_CODE_ALLOWED_TOOLS: str = Field(
        default="Read",
        description="headless 允许的 tools，逗号分隔，如 Read 或 Read,Bash",
    )
    CLAUDE_CODE_OUTPUT_SCHEMA_PATH: str = Field(
        default="resources/schemas/copyright_draft_output.schema.json",
        description="结构化输出 JSON Schema 路径（相对 backend 根目录或绝对路径）",
    )
    CLAUDE_CODE_SETTINGS_FILE: Optional[str] = Field(
        default=None,
        description="可选 --settings JSON 路径（bare 模式注入 API key 等）",
    )
    CLAUDE_CODE_PERMISSION_MODE: Optional[str] = Field(
        default="bypassPermissions",
        description="headless 权限模式，空则不传该参数",
    )

    # 专利草稿：template | claude_code
    PATENT_DRAFT_BACKEND: str = Field(
        default="template",
        description="专利 AI 草稿后端: template, claude_code",
    )
    PATENT_DRAFT_FALLBACK_TO_TEMPLATE: bool = Field(
        default=False,
        description="专利 Claude Code 失败时是否回退模板",
    )
    CLAUDE_CODE_PATENT_SKILL_PROMPT_FILE: str = Field(
        default="resources/skills/patent-application/SKILL.md",
        description="专利技能系统提示文件",
    )
    CLAUDE_CODE_PATENT_OUTPUT_SCHEMA_PATH: str = Field(
        default="resources/schemas/patent_draft_output.schema.json",
        description="专利结构化输出 JSON Schema",
    )

    # 商标草稿：template | claude_code
    TRADEMARK_DRAFT_BACKEND: str = Field(
        default="template",
        description="商标 AI 草稿后端: template, claude_code",
    )
    TRADEMARK_DRAFT_FALLBACK_TO_TEMPLATE: bool = Field(
        default=False,
        description="商标 Claude Code 失败时是否回退模板",
    )
    CLAUDE_CODE_TRADEMARK_SKILL_PROMPT_FILE: str = Field(
        default="resources/skills/trademark-application/SKILL.md",
        description="商标技能系统提示文件",
    )
    CLAUDE_CODE_TRADEMARK_OUTPUT_SCHEMA_PATH: str = Field(
        default="resources/schemas/trademark_draft_output.schema.json",
        description="商标结构化输出 JSON Schema",
    )

    # 源码拉取（Git / 直链 zip）
    SOURCE_FETCH_ALLOWED_HOSTS: str = Field(
        default="",
        description="允许拉取的 host 列表，逗号分隔；空表示禁止任何远程源码拉取",
    )
    SOURCE_FETCH_MAX_ZIP_BYTES: int = Field(
        default=100_000_000,
        description="zip 下载最大字节数",
    )
    SOURCE_FETCH_MAX_EXTRACTED_BYTES: int = Field(
        default=500_000_000,
        description="解压后总字节上限",
    )
    SOURCE_FETCH_WORKDIR_BASE: str = Field(
        default="/tmp/ipflow-source-fetch",
        description="源码拉取临时根目录",
    )
    GIT_CLONE_DEPTH: int = Field(default=1, description="git clone --depth")
    
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

    @property
    def backend_root(self) -> Path:
        """backend 包根目录（含 resources）."""
        return Path(__file__).resolve().parent.parent.parent

    def resolve_backend_path(self, path_str: str) -> Path:
        """将相对 backend 根的路径解析为绝对路径."""
        p = Path(path_str)
        if p.is_absolute():
            return p
        return self.backend_root / p

    @property
    def source_fetch_allowed_hosts_list(self) -> list[str]:
        """允许的远程 host 列表."""
        return [
            h.strip().lower()
            for h in self.SOURCE_FETCH_ALLOWED_HOSTS.split(",")
            if h.strip()
        ]

    @property
    def claude_code_allowed_tools_list(self) -> list[str]:
        return [t.strip() for t in self.CLAUDE_CODE_ALLOWED_TOOLS.split(",") if t.strip()]


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例.
    
    Returns:
        Settings: 应用配置实例
    """
    return Settings()
