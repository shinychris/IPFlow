# IPFlow Backend v2.0

基于 FastAPI + SQLModel + PostgreSQL 的知识产权申请管理平台后端。

## 技术栈

- **Python**: 3.12+
- **Web Framework**: FastAPI 0.115+
- **ORM**: SQLModel 0.22+ (基于 SQLAlchemy 2.0)
- **Database**: PostgreSQL 18+
- **Cache**: Redis 7+
- **Task Queue**: Celery + Redis
- **Storage**: MinIO (S3 兼容)
- **Package Manager**: uv

## 快速开始

### 1. 安装依赖

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 2. 启动基础设施

```bash
docker-compose up -d
```

这将启动：
- PostgreSQL 18 (端口 5432)
- Redis 7 (端口 6379)
- MinIO (端口 9000/9001)

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 4. 数据库迁移

```bash
alembic upgrade head
```

### 5. 启动开发服务器

```bash
# 方式1: 直接启动
uvicorn src.ipflow.main:app --reload --port 8000

# 方式2: 使用脚本
./scripts/dev.sh
```

访问: http://localhost:8000/docs (API 文档)

## 开发规范

### TDD 开发流程

1. 先写测试 (Red)
2. 实现功能 (Green)
3. 重构优化 (Refactor)

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_security.py -v

# 运行并生成覆盖率报告
pytest --cov=src/ipflow --cov-report=html
```

### 代码质量

```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .

# 类型检查
mypy src/ipflow

# 运行 pre-commit
pre-commit run --all-files
```

## 项目结构

```
backend/
├── src/ipflow/           # 主代码
│   ├── api/             # API 路由
│   ├── core/            # 核心基础设施
│   ├── models/          # SQLModel 模型
│   ├── services/        # 业务逻辑
│   ├── db/              # 数据库配置
│   ├── tasks/           # Celery 任务
│   └── utils/           # 工具函数
├── tests/               # 测试
├── alembic/             # 数据库迁移
├── scripts/             # 运维脚本
└── pyproject.toml       # 项目配置
```

## API 版本

- **v1**: `/api/v1/` (当前版本)

## 环境要求

- Python 3.12+
- PostgreSQL 18+
- Redis 7+
- Docker & Docker Compose (推荐)

## 许可证

MIT
