# React + Vite → Next.js 16 迁移指南

本文档记录了从 React + Vite 迁移到 Next.js 16 的过程。

## 主要变更

### 1. 项目结构

```
# 新结构 (Next.js 16)
IPFlow/
├── backend/              # Python 后端服务
│   ├── src/
│   ├── tests/
│   ├── alembic/
│   └── scripts/
├── frontend/             # Next.js 前端
│   ├── app/              # App Router
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   ├── stores/
│   ├── api/
│   └── public/           # 静态资源
├── shared/               # 前后端共享类型定义
│   └── schema.ts
├── docs/                 # 文档
├── attached_assets/      # 附件资源
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### 2. 删除的目录

- `server/` - 旧的 Express 服务器（后端已迁移到 Python）
- `script/` - 旧的构建脚本（Next.js 不需要）
- `client/` - 旧的 Vite 前端（已迁移到 frontend）
- `src/` - 已重命名为 `frontend/`

### 3. 路由变化

| 旧路径 (Vite) | 新路径 (Next.js) |
|---------------|------------------|
| `/` | `/` |
| `/projects` | `/projects` |
| `/copyright` | `/copyright` |
| `/patent` | `/patent` |
| `/trademark` | `/trademark` |
| `/project/new` | `/project/new` |
| `/project/:id` | `/project/[id]` |
| `/settings` | `/settings` |
| `/rules` | `/rules` |
| `/help` | `/help` |
| `/login` | `/login` |
| `/register` | `/register` |

### 4. 代码变更

#### 路由导航
```tsx
// 旧 (wouter)
import { useLocation, Link } from "wouter";
const [, setLocation] = useLocation();
setLocation("/projects");

// 新 (Next.js)
import { useRouter } from "next/navigation";
import Link from "next/link";
const router = useRouter();
router.push("/projects");
```

#### 当前路径
```tsx
// 旧 (wouter)
const [location] = useLocation();

// 新 (Next.js)
import { usePathname } from "next/navigation";
const pathname = usePathname();
```

#### 查询参数
```tsx
// 新 (Next.js)
import { useSearchParams } from "next/navigation";
const searchParams = useSearchParams();
const type = searchParams.get("type");
```

### 5. 配置变更

#### TypeScript
- 更新 `tsconfig.json` - 路径从 `src/*` 改为 `frontend/*`

#### Tailwind CSS
- 更新 `tailwind.config.ts` - content 路径改为 `frontend/**/*`
- CSS 文件位于 `frontend/app/globals.css`

#### Next.js
- `next.config.ts` - 静态导出配置
- API 代理到 Python 后端 (localhost:8000)

## 开发命令

```bash
# 安装依赖
pnpm install

# 开发模式 (端口 3000)
pnpm dev

# 同时启动前后端
make dev

# 构建
pnpm build

# 生产模式
pnpm start
```

## 注意事项

1. **客户端组件**: 所有使用 hooks 的组件必须添加 `"use client"` 指令
2. **服务端组件**: Next.js 默认使用服务端组件，静态页面可以移除 `"use client"`
3. **API 代理**: Next.js 开发服务器配置了 API 代理到 Python 后端 (端口 8000)
4. **图片优化**: 静态导出配置了 `unoptimized: true`
5. **路径别名**: `@/*` 指向 `frontend/*`，`@shared/*` 指向 `shared/*`
