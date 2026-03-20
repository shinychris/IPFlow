# IPFlow v2.0 - 知识产权申请管理平台

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="version">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="python">
  <img src="https://img.shields.io/badge/node-18%2B-green.svg" alt="node">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
</p>

## 项目简介

IPFlow 是一个全栈式知识产权申请管理平台，支持**软件著作权、专利、商标**三种业务类型的自动化文档生成与合规检查。系统采用多租户 SaaS 架构，支持组织协作、分级订阅和完整的管理后台。

**核心功能:**
- 📝 **软件著作权申请**: 5步向导流程，自动代码抽取（60页），操作手册生成
- 🔬 **专利申请**: 发明专利/实用新型/外观设计，权利要求书与说明书辅助撰写
- 🏷️ **商标注册**: Nice 分类查询（45类），图样上传，材料准备
- 🏢 **组织协作**: 多租户架构，支持团队成员协作
- 💳 **订阅计费**: 分级订阅计划，灵活的资源配额
- 📊 **管理后台**: 完整的超级管理员功能
- 🔍 **审计监控**: 全链路操作日志与健康监控

---

## 技术栈

### 后端 (Backend)
| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.12+ | 编程语言 |
| **FastAPI** | 0.115+ | Web框架，异步高性能API |
| **SQLModel** | 0.0.22+ | ORM，类型安全的SQLAlchemy封装 |
| **PostgreSQL** | 18+ | 主数据库 |
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
| **pnpm** | latest | 包管理器 |

---

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+
- PostgreSQL 18+
- Redis 7+
- MinIO (用于文件存储)

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/your-org/ipflow.git
cd ipflow
```

#### 2. 使用 Docker 启动基础设施（推荐）
```bash
docker compose up -d db redis minio

# 这将启动:
# - PostgreSQL 数据库 (端口: 5432)
# - Redis 缓存 (端口: 6379)
# - MinIO 对象存储 (端口: 9000/9001)
```

#### 3. 后端配置
```bash
cd backend

# 创建虚拟环境 (使用 uv)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
uv pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等
```

#### 4. 数据库迁移
```bash
cd backend

# 创建数据库表
alembic upgrade head

# 或使用自动创建（开发环境）
python -c "import asyncio; from ipflow.main import create_tables; asyncio.run(create_tables())"
```

#### 5. 前端配置
```bash
cd frontend

# 安装依赖
pnpm install  # 或 npm install

# 配置环境变量
cp .env.example .env.local
```

#### 6. 启动服务
```bash
# 后端（终端1）
cd backend
uvicorn ipflow.main:app --reload --port 8000

# 前端（终端2）
cd frontend
pnpm dev  # 或 npm run dev
```

访问 http://localhost:3000 开始使用

---

## 项目结构

```
ipflow/
├── backend/                    # Python FastAPI 后端
│   ├── src/ipflow/
│   │   ├── api/v1/            # API路由
│   │   │   ├── auth.py        # 认证
│   │   │   ├── projects.py    # 项目管理
│   │   │   ├── copyright/     # 软著模块
│   │   │   │   ├── software_info.py
│   │   │   │   ├── code_bundles.py
│   │   │   │   ├── manuals.py
│   │   │   │   └── export.py
│   │   │   ├── patents/       # 专利模块
│   │   │   │   ├── patent_info.py
│   │   │   │   ├── claims.py
│   │   │   │   ├── description.py
│   │   │   │   └── export.py
│   │   │   ├── trademarks/    # 商标模块
│   │   │   │   ├── trademark_info.py
│   │   │   │   ├── nice_classification.py
│   │   │   │   └── export.py
│   │   │   ├── organizations.py # 组织管理
│   │   │   ├── subscriptions.py # 订阅管理
│   │   │   └── admin.py       # 管理后台
│   │   ├── core/              # 核心功能（安全、中间件、监控）
│   │   ├── db/                # 数据库配置
│   │   ├── models/            # SQLModel模型
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── copyright.py
│   │   │   ├── patent.py      # 专利模型
│   │   │   ├── trademark.py   # 商标模型
│   │   │   ├── organization.py
│   │   │   ├── subscription.py
│   │   │   └── audit.py
│   │   ├── services/          # 业务逻辑服务
│   │   │   ├── copyright/
│   │   │   │   ├── code_processor.py
│   │   │   │   ├── export_generator.py
│   │   │   │   └── compliance_checker.py
│   │   │   ├── quota_service.py
│   │   │   └── subscriptions/
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试用例
│   ├── alembic/               # 数据库迁移
│   ├── pyproject.toml         # Python依赖
│   └── docker-compose.yml     # 开发环境
│
├── frontend/                  # Next.js 16 前端
│   ├── app/                   # App Router
│   │   ├── (auth)/           # 认证路由组
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/      # 主应用路由组
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── projects/
│   │   │   ├── copyright/
│   │   │   ├── patent/
│   │   │   ├── trademark/
│   │   │   ├── project/
│   │   │   │   ├── new/
│   │   │   │   └── [id]/
│   │   │   ├── settings/
│   │   │   ├── rules/
│   │   │   └── help/
│   │   ├── layout.tsx        # 根布局
│   │   ├── page.tsx          # 首页
│   │   └── globals.css       # 全局样式
│   ├── components/           # UI组件
│   │   ├── ui/              # shadcn/ui 组件
│   │   ├── app-sidebar.tsx
│   │   ├── project-card.tsx
│   │   └── ...
│   ├── api/                  # API客户端
│   ├── stores/               # Zustand状态管理
│   ├── types/                # TypeScript类型
│   ├── lib/                  # 工具函数
│   └── public/               # 静态资源
│
├── shared/                     # 前后端共享类型
│   └── schema.ts
│
├── docs/                       # 设计文档
│   ├── IPFlow-v2-架构设计文档.md
│   ├── IPFlow-v2-开发任务清单.md
│   └── IPFlow-产品说明文档.md
│
├── docker-compose.yml          # 生产环境
├── README.md                   # 本文件
└── CHANGELOG.md                # 变更日志
```

---

## API文档

启动后端服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 主要API模块

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth/*` | 登录、注册、Token刷新 |
| 项目 | `/api/v1/projects/*` | 项目管理CRUD |
| 软著 | `/api/v1/copyright/*` | 软件著作权材料处理 |
| 专利 | `/api/v1/patents/*` | 专利申请与管理 |
| 商标 | `/api/v1/trademarks/*` | 商标注册与管理 |
| 合规 | `/api/v1/compliance/*` | 合规性检查 |
| 上传 | `/api/v1/uploads/*` | 文件上传管理 |
| 组织 | `/api/v1/organizations/*` | 组织与成员管理 |
| 订阅 | `/api/v1/subscriptions/*` | 订阅与计费 |
| 管理 | `/api/v1/admin/*` | 超级管理员功能 |

**API 统计**: 100+ 个端点，完整的 RESTful API

---

## 功能模块

### M1: 后端基础架构 ✅
- [x] FastAPI + SQLModel 项目架构
- [x] JWT 认证系统（access/refresh token）
- [x] 用户管理系统
- [x] 数据库模型设计
- [x] Docker 开发环境
- [x] 结构化日志与异常处理

### M2: 核心功能 ✅
- [x] 项目管理（CRUD、复制、筛选）
- **软件著作权**
  - [x] 软件信息管理
  - [x] 代码处理引擎（40+ 语言支持）
  - [x] 前30页+后30页分页生成
  - [x] 操作说明书编辑
  - [x] 合规检查
  - [x] 导出功能
- **专利申请**（新增）
  - [x] 专利信息管理（发明/实用新型/外观设计）
  - [x] 权利要求书编写
  - [x] 说明书编辑
  - [x] 附图管理
  - [x] 导出功能
- **商标注册**（新增）
  - [x] 商标信息管理（6种类型）
  - [x] 尼斯分类选择（45类）
  - [x] 商标图样上传
  - [x] 导出功能

### M3: 前端重构 ✅
- [x] Zustand 状态管理
- [x] TanStack Query 服务端状态
- [x] TypeScript 类型系统
- [x] shadcn/ui 组件库
- [x] 响应式设计
- [x] 代码预览组件
- [x] 富文本编辑器
- [x] 文件上传组件

### M4: 商业化功能 ✅
- [x] 多租户架构
- [x] 组织与成员管理
- [x] 角色权限控制（RBAC）
- [x] 订阅与计费系统（5种计划）
- [x] 限额控制服务
- [x] 管理后台
- [x] 审计日志
- [x] 健康监控

---

## 订阅计划

### 按次付费
适合偶尔需要申请的用户
- **价格**: ¥19.0/次
- **项目数量**: 1个
- **存储空间**: 500MB
- **功能**: 软著申请主流程，基础代码处理与导出，支付后立即可用，未通过可联系客服退款

### 订阅套餐

| 套餐 | 基础版 | 专业版 ⭐ | 企业版 | 代理机构版 |
|-----|--------|---------|--------|------------|
| **月付价格** | ¥49/月 | ¥199/月 | ¥999/月 | ¥1999/月 |
| **年付价格** | ¥490/年 | ¥1990/年 | ¥9990/年 | ¥19990/年 |
| **年付节省** | 省17% | 省17% | 省17% | 省17% |
| **项目数量** | 10个 | 10个 | 100个 | 500个 |
| **存储空间** | 1GB | 10GB | 100GB | 1TB |
| **团队成员** | 1人 | 3人 | 无限 | 20人 |
| **软著申请** | ✅ | ✅ | ✅ | ✅ |
| **专利申请** | - | ✅ | ✅ | ✅ |
| **商标申请** | - | ✅ | ✅ | ✅ |
| **AI辅助生成** | ✅ | ✅ | ✅ | ✅ |
| **高级代码处理** | ✅ | ✅ | ✅ | ✅ |
| **批量导出** | - | ✅ | ✅ | ✅ |
| **团队协作** | - | ✅ | ✅ | ✅ |
| **优先支持** | - | ✅ | ✅ | ✅ |
| **AI智能优化** | - | ✅ | ✅ | ✅ |
| **专属客户经理** | - | - | ✅ | ✅ |
| **SLA服务保障** | - | - | ✅ | - |
| **定制化开发** | - | - | ✅ | - |
| **私有化部署** | - | - | ✅ | - |
| **客户管理** | - | - | - | ✅ |
| **白标定制** | - | - | - | ✅ |
| **API接口** | - | - | - | ✅ |
| **批量处理工具** | - | - | - | ✅ |

**推荐方案**：
- 💡 **个人开发者**：按次付费（偶尔使用）或基础版（频繁使用）
- ⭐ **小型团队**：专业版（最推荐，性价比最高）
- 🏢 **中大型企业**：企业版（完整功能和专属服务）
- 🏛️ **知识产权代理机构**：代理机构版（专业工具和白标定制）

---

## 开发文档

- [架构设计文档](docs/IPFlow-v2-架构设计文档.md)
- [产品说明文档](docs/IPFlow-产品说明文档.md)
- [开发任务清单](docs/IPFlow-v2-开发任务清单.md)

---

## 部署指南

### Docker 部署（推荐）

```bash
# 生产环境
docker-compose -f docker-compose.yml up -d
```

### 手动部署

```bash
# 后端
cd backend
pip install -e "."
uvicorn src.ipflow.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
pnpm install
pnpm build
# 将 .next 目录部署到 Node.js 服务器
```

---

## 测试

### 后端测试
```bash
cd backend

# 运行所有测试
pytest -v

# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v

# 带覆盖率
pytest --cov=src --cov-report=html
```

### 前端测试
```bash
cd frontend

# 运行测试
pnpm test

# 构建检查
pnpm build
```

### 测试结果
- **单元测试**: 121 passed ✅
- **集成测试**: 进行中 ⚠️
- **前端构建**: 成功 ✅

---

## 环境变量

### 后端 (.env)
```bash
# 应用
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-secret-key

# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ipflow

# Redis
REDIS_URL=redis://localhost:6379/0

# 存储
STORAGE_TYPE=minio
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 前端 (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 许可证

[MIT](LICENSE)

---

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

---

## 联系方式

- 项目主页: https://github.com/your-org/ipflow
- 问题反馈: https://github.com/your-org/ipflow/issues
- 邮箱: support@ipflow.com

---

<p align="center">
  Made with ❤️ by IPFlow Team
</p>
