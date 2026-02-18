"""Alembic 环境配置."""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# 导入应用配置和模型
from ipflow.config import get_settings
from ipflow.models import *  # noqa: F403
from sqlmodel import SQLModel

# Alembic 配置对象
config = context.config
settings = get_settings()

# 从配置文件中设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 模型元数据
target_metadata = SQLModel.metadata

# 使用同步数据库 URL（alembic 需要同步连接）
config.set_main_option("sqlalchemy.url", settings.sync_database_url)


def run_migrations_offline() -> None:
    """离线运行迁移.
    
    使用 URL 配置而不是 Engine。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线运行迁移（同步模式）."""
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
