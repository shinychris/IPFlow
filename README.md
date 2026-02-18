# IPFlow v2.0 - 知识产权申请助手

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="version">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="python">
  <img src="https://img.shields.io/badge/node-18%2B-green.svg" alt="node">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
</p>

## 项目简介

IPFlow 是一个全栈式知识产权申请管理平台，支持软件著作权、专利、商标三种业务类型的自动化文档生成与合规检查。系统采用多租户SaaS架构，支持组织协作、分级订阅和完整的管理后台。

**核心功能:**
- 📝 **软件著作权申请**: 5步向导流程，自动代码抽取（60页），操作手册生成
- 🔬 **专利申请**: 权利要求书与说明书辅助撰写
- 🏷️ **商标注册**: Nice分类查询与材料准备
- 🏢 **组织协作**: 多租户架构，支持团队成员协作
- 💳 **订阅计费**: 分级订阅计划，灵活的资源配额
- 📊 **管理后台**: 完整的超级管理员功能
- 🔍 **审计监控**: 全链路操作日志与健康监控

## 技术栈

### 后端 (Backend)
| 技术 | 用途 |
|------|------|
| **FastAPI** | Web框架，异步高性能API |
| **SQLModel** | ORM，类型安全的SQLAlchemy封装 |
| **PostgreSQL** | 主数据库 |
| **Redis** | 缓存与会话存储 |
| **MinIO** | 对象存储 |
| **Celery** | 异步任务队列 |
| **Pytest** | 测试框架 |

### 前端 (Frontend)
| 技术 | 用途 |
|------|------|
| **React 18** | UI框架 |
| **TypeScript** | 类型安全 |
| **Zustand** | 状态管理 |
| **Axios** | HTTP客户端 |
| **shadcn/ui** | UI组件库 |
| **Tailwind CSS** | 样式框架 |
| **Vite** | 构建工具 |

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- MinIO (可选，用于文件存储)

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/your-org/ipflow.git
cd ipflow
```

#### 2. 后端配置
```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等
```

#### 3. 前端配置
```bash
cd ../client

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
```

#### 4. 数据库迁移
```bash
cd ../backend

# 创建数据库表
alembic upgrade head

# 或使用自动创建（开发环境）
python -c "import asyncio; from ipflow.main import create_tables; asyncio.run(create_tables())"
```

#### 5. 启动服务
```bash
# 后端（终端1）
cd backend
uvicorn ipflow.main:app --reload --port 8000

# 前端（终端2）
cd client
npm run dev
```

访问 http://localhost:5173 开始使用

## 项目结构

```
ipflow/
├── backend/                    # 后端服务
│   ├── src/ipflow/
│   │   ├── api/v1/            # API路由
│   │   ├── core/              # 核心功能（安全、中间件、监控）
│   │   ├── db/                # 数据库配置
│   │   ├── models/            # SQLModel模型
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── services/          # 业务逻辑服务
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试用例
│   └── pyproject.toml         # Python依赖
│
├── client/                     # 前端应用
│   ├── src/
│   │   ├── components/        # UI组件
│   │   ├── pages/             # 页面组件
│   │   ├── stores/            # Zustand状态管理
│   │   ├── types/             # TypeScript类型
│   │   └── lib/               # 工具函数
│   └── package.json
│
├── docs/                       # 文档
│   ├── architecture.md        # 架构设计
│   ├── api.md                 # API文档
│   ├── deployment.md          # 部署指南
│   └── development.md         # 开发指南
│
└── docker-compose.yml          # Docker编排
```

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
| 合规 | `/api/v1/compliance/*` | 合规性检查 |
| 组织 | `/api/v1/organizations/*` | 组织与成员管理 |
| 订阅 | `/api/v1/subscriptions/*` | 订阅与计费 |
| 管理 | `/api/v1/admin/*` | 超级管理员功能 |

## 功能模块

### M1: 基础架构 ✅
- [x] JWT认证系统
- [x] 用户管理
- [x] 数据库模型设计
- [x] Docker开发环境

### M2: 核心功能 ✅
- [x] 项目管理
- [x] 代码处理（60页抽取）
- [x] 操作手册生成
- [x] 合规检查
- [x] PDF导出

### M3: 前端重构 ✅
- [x] Zustand状态管理
- [x] TypeScript类型系统
- [x] 组件库完善
- [x] 响应式设计

### M4: 商业化功能 ✅
- [x] 多租户架构
- [x] 组织与成员管理
- [x] 订阅与计费系统
- [x] 限额控制
- [x] 管理后台
- [x] 审计日志
- [x] 监控告警

## 开发文档

详细开发指南请查看：
- [架构设计文档](docs/architecture.md)
- [开发指南](docs/development.md)
- [API文档](docs/api.md)
- [数据库文档](docs/database.md)

## 部署指南

支持多种部署方式：
- [Docker部署](docs/deployment.md#docker部署)
- [Kubernetes部署](docs/deployment.md#kubernetes部署)
- [传统服务器部署](docs/deployment.md#传统服务器部署)

快速部署：
```bash
docker-compose up -d
```

## 测试

```bash
# 后端测试
cd backend
pytest -v

# 前端测试
cd client
npm test
```

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

[MIT](LICENSE)

## 联系方式

- 项目主页: https://github.com/your-org/ipflow
- 问题反馈: https://github.com/your-org/ipflow/issues
- 邮箱: support@ipflow.com

---

<p align="center">
  Made with ❤️ by IPFlow Team
</p>
