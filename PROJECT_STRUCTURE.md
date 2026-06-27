# IPFlow 项目结构

本文档说明 IPFlow 项目的目录结构。IPFlow 的核心定位是知识产权申报材料辅助生成、整理、合规检查与导出工具。

## 目录概览

```
IPFlow/
├── backend/              # Python FastAPI 后端
├── frontend/             # Next.js 16 前端
├── shared/               # 前后端共享类型定义
├── docs/                 # 项目文档
├── attached_assets/      # 附件资源
├── next.config.ts        # Next.js 配置
├── tailwind.config.ts    # Tailwind CSS 配置
├── tsconfig.json         # TypeScript 配置
├── package.json          # Node.js 依赖
└── Makefile              # 开发命令
```

## 后端 (backend/)

Python FastAPI 后端服务。

```
backend/
├── src/ipflow/           # 主应用代码
│   ├── api/v1/          # API 路由
│   ├── core/            # 核心功能（安全、中间件）
│   ├── models/          # SQLModel 数据模型
│   ├── services/        # 业务逻辑服务
│   └── main.py          # 应用入口
├── tests/               # 测试用例
├── alembic/             # 数据库迁移
├── scripts/             # 脚本工具
├── pyproject.toml       # Python 依赖配置
└── docker-compose.yml   # 开发环境配置
```

## 前端 (frontend/)

Next.js 16 + React 19 前端应用。

```
frontend/
├── app/                  # App Router (Next.js 13+)
│   ├── (auth)/          # 认证路由组
│   │   ├── login/       # 登录页面
│   │   └── register/    # 注册页面
│   ├── (dashboard)/     # 主应用路由组
│   │   ├── page.tsx     # 工作台首页
│   │   ├── projects/    # 项目列表
│   │   ├── copyright/   # 软著申请
│   │   ├── patent/      # 专利申请
│   │   ├── trademark/   # 商标申请
│   │   ├── project/     # 项目详情/创建
│   │   ├── settings/    # 设置页面
│   │   ├── rules/       # 申请规范
│   │   └── help/        # 帮助文档
│   ├── layout.tsx       # 根布局
│   ├── page.tsx         # 首页
│   ├── globals.css      # 全局样式
│   └── providers.tsx    # 全局 Providers
├── components/          # React 组件
│   ├── ui/             # shadcn/ui 组件
│   └── ...             # 业务组件
├── api/                # API 客户端
├── stores/             # Zustand 状态管理
├── types/              # TypeScript 类型
├── lib/                # 工具函数
├── hooks/              # 自定义 Hooks
└── public/             # 静态资源
```

## 共享类型 (shared/)

前后端共享的 TypeScript 类型定义。

```
shared/
└── schema.ts           # 数据模型、类型、枚举
```

## 文档 (docs/)

项目相关文档。

```
docs/
├── API_ENDPOINTS.md
├── architecture.md
├── database.md
├── deployment.md
├── development.md
└── ...
```

## 开发命令

```bash
# 安装依赖
make install

# 启动开发服务器（前后端）
make dev

# 仅启动后端
cd backend && uvicorn ipflow.main:app --reload --host 0.0.0.0 --port 8000

# 仅启动前端
pnpm dev

# 构建
pnpm build

# 运行测试
make test
```

## 技术栈

### 后端
- **Python** 3.12+
- **FastAPI** 0.115+
- **SQLModel** / SQLAlchemy
- **PostgreSQL** 14+
- **Redis** 7+
- **MinIO** 对象存储

### 前端
- **Next.js** 16
- **React** 19
- **TypeScript** 5
- **Tailwind CSS** 3.4
- **shadcn/ui**
- **Zustand** 状态管理
- **TanStack Query** 数据获取

## 注意事项

1. **前端路径别名**: `@/*` 指向 `frontend/*`，`@shared/*` 指向 `shared/*`
2. **开发端口**: 前端 `3000`，后端 `8000`
3. **API 代理**: Next.js 开发服务器代理 `/api/*` 到后端
4. **静态导出**: 使用 `output: 'export'` 配置
