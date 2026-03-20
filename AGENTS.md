# IPFlow - Agent Development Guide

> 本文档专为 AI Coding Agent 设计，包含项目架构、开发规范和重要实现细节。
> 语言：中文（项目主要使用中文注释和文档）

---

## 1. 项目概述

**IPFlow** 是一个全栈式知识产权申请管理平台，支持**软件著作权、专利、商标**三种业务类型的自动化文档生成与合规检查。系统采用多租户 SaaS 架构，支持组织协作、分级订阅和完整的管理后台。

### 核心功能
- 📝 **软件著作权申请**: 5步向导流程，自动代码抽取（60页），操作手册生成
- 🔬 **专利申请**: 发明专利/实用新型/外观设计，权利要求书与说明书辅助撰写
- 🏷️ **商标注册**: Nice 分类查询（45类），图样上传，材料准备
- 🏢 **组织协作**: 多租户架构，支持团队成员协作
- 💳 **订阅计费**: 分级订阅计划，灵活的资源配额
- 📊 **管理后台**: 完整的超级管理员功能

---

## 2. 技术栈

### 后端 (Backend)
| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.12+ | 编程语言 |
| **FastAPI** | 0.115+ | Web框架，异步高性能API |
| **SQLModel** | 0.0.22+ | ORM，类型安全的SQLAlchemy封装 |
| **PostgreSQL** | 15+ | 主数据库 |
| **Redis** | 7+ | 缓存与会话存储 |
| **MinIO** | latest | 对象存储 |
| **Celery** | 5.4+ | 异步任务队列 |
| **Pytest** | 8.3+ | 测试框架 |
| **uv** | 0.5+ | Python 包管理 |

### 前端 (Frontend)
| 技术 | 版本 | 用途 |
|------|------|------|
| **Next.js** | 16+ | React框架，App Router |
| **React** | 19+ | UI框架 |
| **TypeScript** | 5.0+ | 类型安全 |
| **Zustand** | 5.0+ | 状态管理 |
| **TanStack Query** | 5.0+ | 服务端状态管理 |
| **shadcn/ui** | latest | UI组件库 |
| **Tailwind CSS** | 3.4+ | 样式框架 |

---

## 3. 项目结构

```
ipflow/
├── backend/                    # Python FastAPI 后端
│   ├── src/ipflow/            # 主应用代码
│   │   ├── api/v1/           # API路由
│   │   │   ├── auth.py       # 认证
│   │   │   ├── projects.py   # 项目管理
│   │   │   ├── copyright/    # 软著模块
│   │   │   ├── patents/      # 专利模块
│   │   │   ├── trademarks/   # 商标模块
│   │   │   ├── organizations.py
│   │   │   ├── subscriptions.py
│   │   │   └── admin.py      # 管理后台
│   │   ├── core/             # 核心功能（安全、中间件、监控）
│   │   ├── db/               # 数据库配置
│   │   ├── models/           # SQLModel模型
│   │   ├── services/         # 业务逻辑服务
│   │   └── main.py           # 应用入口
│   ├── tests/                # 测试用例
│   ├── alembic/              # 数据库迁移
│   └── pyproject.toml        # Python依赖
│
├── frontend/                   # Next.js 16 前端
│   ├── app/                  # App Router
│   │   ├── (auth)/          # 认证路由组
│   │   ├── (dashboard)/     # 主应用路由组
│   │   └── (marketing)/     # 营销页面
│   ├── components/          # UI组件
│   ├── api/                 # API客户端
│   ├── stores/              # Zustand状态管理
│   ├── types/               # TypeScript类型
│   └── lib/                 # 工具函数
│
├── shared/                     # 前后端共享类型定义
│   └── schema.ts             # Drizzle ORM 模型定义
│
└── docs/                       # 项目文档
```

---

## 4. 开发命令

### 项目根目录命令
```bash
# 安装所有依赖
make install

# 启动开发服务器（前后端）
make dev

# 仅启动后端
cd backend && uvicorn ipflow.main:app --reload --host 0.0.0.0 --port 8000

# 仅启动前端
pnpm dev              # http://localhost:3000

# 构建
make build

# 运行测试
make test             # 运行所有测试
make test-backend     # 仅运行后端测试

# 代码质量检查
make lint             # ruff + mypy
make format           # black + isort
```

### 后端专用命令
```bash
cd backend

# 数据库迁移
alembic upgrade head           # 升级到最新
alembic downgrade -1           # 回滚一级

# 测试
pytest -v                      # 运行所有测试
pytest --cov=src --cov-report=html  # 带覆盖率

# 代码检查
ruff check src/ tests/
mypy src/
black src/ tests/
isort src/ tests/
```

### 前端专用命令
```bash
cd frontend

# 开发
pnpm dev

# 构建
pnpm build

# 类型检查
pnpm check            # tsc

# 代码检查
pnpm lint
```

---

## 5. 代码风格规范

### Python 规范

**使用工具**: ruff (lint + format), mypy (type check)

```python
# 必须添加类型注解
async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID
) -> Optional[User]:
    """根据ID获取用户.
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        用户对象，如果不存在则返回 None
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

**配置详情** (pyproject.toml):
- Line length: 100
- Quote style: double
- Target Python: 3.12
- 使用 Google docstring convention

### TypeScript 规范

**使用严格类型，避免 `any`**

```typescript
interface UserProps {
  id: string;
  name: string;
  email: string;
}

/**
 * 用户卡片组件
 * @param props - 组件属性
 */
export function UserCard({ id, name, email }: UserProps) {
  return (
    <div className="user-card">
      <h3>{name}</h3>
      <p>{email}</p>
    </div>
  );
}
```

### 路径别名

| 别名 | 指向 |
|------|------|
| `@/*` | `frontend/*` |
| `@shared/*` | `shared/*` |

---

## 6. 数据库模型

使用 **SQLModel** (后端) 和 **Drizzle ORM** (shared 类型定义)。

### 核心实体关系

```
User (用户)
  └── OrganizationMember (组织成员)
       └── Organization (组织)
            ├── Project (项目)
            │    ├── SoftwareInfo (软著信息)
            │    ├── PatentInfo (专利信息)
            │    ├── TrademarkInfo (商标信息)
            │    ├── CodeBundle (代码包)
            │    ├── ManualBundle (说明书)
            │    └── ExportPackage (导出包)
            ├── Subscription (订阅)
            │    └── Plan (计划)
            └── AuditLog (审计日志)
```

### 项目类型枚举
```python
project_types = ["copyright", "patent", "trademark"]

patent_types = ["invention", "utility_model", "design"]
trademark_types = ["text", "graphic", "combined", "3d", "sound", "color"]
```

---

## 7. API 架构

### 路由结构
```
/api/v1/
  ├── /auth/*          # 认证 (login, register, refresh, logout)
  ├── /projects/*      # 项目管理
  ├── /copyright/*     # 软著申请
  ├── /patents/*       # 专利申请
  ├── /trademarks/*    # 商标注册
  ├── /compliance/*    # 合规检查
  ├── /uploads/*       # 文件上传
  ├── /organizations/* # 组织管理
  ├── /subscriptions/* # 订阅与计费
  └── /admin/*         # 超级管理员功能
```

### 认证方式
- **JWT Token**: access token (30分钟) + refresh token (7天)
- **Token 黑名单**: 存储在 Redis 中
- **请求头**: `Authorization: Bearer <token>`

### 响应格式
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

错误响应:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数错误",
    "details": { ... }
  }
}
```

---

## 8. 测试策略

### 后端测试
```bash
cd backend

# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v

# 带覆盖率
pytest --cov=src --cov-report=html
```

**测试文件命名**: `test_*.py`

**测试标记**:
- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.slow` - 慢速测试

### 测试配置
- pytest 配置在 `pyproject.toml`
- conftest.py 包含共享 fixtures
- 使用 factory-boy 创建测试数据

---

## 9. 环境变量

### 后端 (.env)
```bash
# 必需配置
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ipflow
REDIS_URL=redis://localhost:6379/0

# MinIO / S3 对象存储
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=ipflow

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI/LLM 配置
ENABLE_AI_ASSISTANT=true
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### 前端 (.env.local)
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 10. 部署流程

### Docker 部署（推荐）
```bash
# 开发环境
docker-compose up -d

# 包含服务:
# - PostgreSQL (端口: 5432)
# - Redis (端口: 6379)
# - MinIO (端口: 9000/9001)
# - Backend (端口: 8000)
# - Frontend (端口: 80)
```

### 手动部署
```bash
# 后端
cd backend
pip install -e "."
uvicorn ipflow.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
pnpm install
pnpm build
# 部署 dist 目录到静态服务器
```

---

## 11. 开发约定

### Git 提交规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**: feat, fix, docs, style, refactor, perf, test, chore
**Scope**: backend, frontend, db, api, auth, copyright, org, billing

**示例**:
```
feat(backend): 添加用户注册功能

- 实现用户模型
- 添加注册 API
- 发送验证邮件

Closes #123
```

### 代码审查清单
- [ ] 代码符合项目规范
- [ ] 有足够测试覆盖
- [ ] 所有测试通过
- [ ] 没有安全漏洞
- [ ] 文档已更新

---

## 12. 重要文件索引

| 文件 | 用途 |
|------|------|
| `backend/pyproject.toml` | Python 依赖、工具配置 |
| `backend/src/ipflow/main.py` | FastAPI 应用入口 |
| `backend/src/ipflow/config.py` | Pydantic Settings 配置 |
| `backend/src/ipflow/models/` | SQLModel 数据模型 |
| `backend/src/ipflow/api/v1/` | API 路由定义 |
| `frontend/package.json` | Node.js 依赖 |
| `frontend/app/` | Next.js App Router |
| `frontend/components/ui/` | shadcn/ui 组件 |
| `shared/schema.ts` | 共享类型定义 (Drizzle ORM) |
| `docker-compose.yml` | Docker 服务编排 |
| `Makefile` | 开发命令快捷方式 |

---

## 13. 常见问题

### 数据库迁移失败
```bash
# 检查 alembic 版本
alembic current
alembic history

# 手动标记版本
alembic stamp head
```

### Python 依赖冲突
```bash
# 使用 uv 重新安装
cd backend
rm -rf .venv
uv venv
uv pip install -e ".[dev]"
```

### 前端类型错误
```bash
cd frontend
pnpm check  # 查看详细错误
```

---

## 14. 扩展资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [Next.js 文档](https://nextjs.org/docs)
- [shadcn/ui 文档](https://ui.shadcn.com/)

---

**最后更新**: 2026-03-01

**文档语言**: 中文（与项目主要文档保持一致）
