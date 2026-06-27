"""仿真测试用后端启动器。

在不修改生产配置的前提下，临时放宽 ``DATABASE_URL`` 字段类型，
使其支持 SQLite（``sqlite+aiosqlite``），从而在没有 PostgreSQL/Redis/MinIO
的本地环境也能启动后端进行仿真可用性测试。

仅用于仿真测试，不影响生产部署（生产仍要求 Postgres）。
"""

import os

# 仿真环境变量（优先级低于真实 .env，仅当 .env 缺失时生效）
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./ipflow_sim.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("STORAGE_TYPE", "local")
os.environ.setdefault("STORAGE_BASE_PATH", "/tmp/ipflow-storage")
os.environ.setdefault("ENABLE_AI_ASSISTANT", "false")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "sim-test-secret-key")
os.environ.setdefault("ENABLE_REGISTRATION", "true")

# 放宽 DATABASE_URL 类型校验为 str（支持 SQLite）
from ipflow import config as _cfg  # noqa: E402

_db_field = _cfg.Settings.model_fields["DATABASE_URL"]
_db_field.annotation = str
_cfg.Settings.model_rebuild(force=True)


# ---------------------------------------------------------------------------
# SQLite 适配：让 SQLite 正确处理 UUID 与 JSON
#
# 生产环境使用 PostgreSQL，UUID/JSON 为原生类型，无此问题。以下适配仅服务于
# 仿真测试（SQLite），使本地无 Postgres 时也能跑通业务流程。
# ---------------------------------------------------------------------------
def _install_sqlite_uuid_adapter() -> None:
    import json
    from uuid import UUID

    from sqlalchemy import event, pool
    from sqlalchemy.types import TypeDecorator, CHAR, String
    from sqlalchemy.engine import Engine

    # 自定义 UUID 类型：SQLite 用 CHAR(36) 存储，读取时转回 UUID 对象
    class SQLiteUUID(TypeDecorator):
        impl = CHAR(36)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            if isinstance(value, UUID):
                return str(value)
            return str(UUID(value))

        def process_result_value(self, value, dialect):
            if value is None:
                return None
            if isinstance(value, UUID):
                return value
            return UUID(value)

    # 替换 SQLModel/SQLAlchemy 默认的 UUID 类型解析（针对 SQLite）
    from sqlalchemy import types

    _orig_uuid_result = types.Uuid.result_processor

    def _patched_uuid_result(self, dialect, coltype):
        if dialect.name == "sqlite":
            def process(value):
                if value is None:
                    return None
                if isinstance(value, UUID):
                    return value
                return UUID(value)
            return process
        return _orig_uuid_result(self, dialect, coltype)

    types.Uuid.result_processor = _patched_uuid_result

    # 让原生 UUID 类型（SQLAlchemy 2.0 的 Uuid）在 SQLite 下用 String 存储并回转
    from uuid import UUID as _PyUUID

    _orig_bind = types.Uuid.bind_processor

    def _patched_bind(self, dialect):
        # SQLite 无原生 UUID，走字符型存储；兼容 str 与 UUID 两种入参
        character_based = (
            not dialect.supports_native_uuid or not self.native_uuid
        )
        if character_based and self.as_uuid:

            def process(value):
                if value is None:
                    return None
                if isinstance(value, _PyUUID):
                    return value.hex
                # 字符串形式的 UUID：规范化为 32 位 hex
                return _PyUUID(str(value)).hex

            return process
        return _orig_bind(self, dialect)

    types.Uuid.bind_processor = _patched_bind
    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        # SQLite 默认不强制外键，开启以贴近生产语义
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


_install_sqlite_uuid_adapter()


if __name__ == "__main__":
    import uvicorn  # noqa: E402

    uvicorn.run(
        "ipflow.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )
