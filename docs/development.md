# IPFlow 开发指南

## 1. 开发环境搭建

### 1.1 前置要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Python | 3.12+ | 后端开发 |
| Node.js | 18+ | 前端开发 |
| PostgreSQL | 18+ | 数据库 |
| Redis | 7+ | 缓存 |
| Git | 最新 | 版本控制 |
| Make | 最新 | 构建工具 |

### 1.2 项目克隆

```bash
# 克隆项目
git clone https://github.com/your-org/ipflow.git
cd ipflow

# 安装 git hooks
./scripts/install-hooks.sh
```

### 1.3 后端环境

```bash
cd backend

# 创建虚拟环境
# 创建虚拟环境（使用 uv）
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装开发依赖
uv pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 配置数据库连接等
```

### 1.4 前端环境

```bash
cd frontend

# 安装依赖
pnpm install

# 配置环境变量
cp .env.example .env.local
```

### 1.5 数据库初始化

```bash
# 创建数据库
createdb ipflow_dev

# 执行迁移
cd backend
alembic upgrade head

# 或使用自动创建（开发环境）
python -c "
import asyncio
from ipflow.main import create_tables
asyncio.run(create_tables())
"

# 创建测试数据
python scripts/seed_data.py
```

### 1.6 启动开发服务器

```bash
# 终端1：启动后端
cd backend
uvicorn src.ipflow.main:app --reload --port 8000

# 终端2：启动前端
cd frontend
pnpm dev

# 访问 http://localhost:3000
```

## 2. 开发规范

### 2.1 代码风格

#### Python (后端)

- **格式化**: Black
- **导入排序**: isort
- **类型检查**: mypy
- **代码检查**: ruff

```bash
# 格式化代码
black src/ tests/
isort src/ tests/

# 类型检查
mypy src/

# 代码检查
ruff check src/ tests/
```

#### TypeScript (前端)

- **格式化**: Prettier
- **代码检查**: ESLint

```bash
# 格式化代码
npm run format

# 代码检查
npm run lint
```

### 2.2 Git 工作流

```
main 分支 (生产环境)
    │
    ├── develop 分支 (开发环境)
    │       │
    │       ├── feature/user-auth (功能分支)
    │       ├── feature/payment
    │       └── bugfix/login-error
    │
    └── hotfix/security-patch (热修复分支)
```

**分支命名规范:**
- 功能分支: `feature/功能描述`
- 修复分支: `bugfix/问题描述`
- 热修复分支: `hotfix/问题描述`
- 发布分支: `release/版本号`

**提交规范:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型说明:
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

示例:
```
feat(auth): 添加用户登录功能

- 实现 JWT Token 生成和验证
- 添加登录表单验证
- 添加错误提示

Closes #123
```

### 2.3 项目结构规范

#### 后端结构

```
backend/src/ipflow/
├── api/
│   └── v1/                    # API 版本控制
│       ├── __init__.py        # 路由聚合
│       └── resource.py        # 资源端点
│
├── models/
│   ├── __init__.py            # 模型导出
│   ├── base.py                # 基础模型
│   ├── user.py                # 用户模型
│   └── ...
│
├── schemas/
│   ├── __init__.py
│   └── resource.py            # Pydantic Schema
│
├── services/
│   ├── __init__.py
│   └── resource_service.py    # 业务逻辑
│
├── core/
│   ├── security.py            # 安全工具
│   ├── exceptions.py          # 自定义异常
│   └── ...
│
└── tests/
    ├── unit/                  # 单元测试
    ├── integration/           # 集成测试
    └── conftest.py            # 测试配置
```

#### 前端结构

```
frontend/
├── components/
│   ├── ui/                    # 基础UI组件
│   ├── layout/                # 布局组件
│   └── features/              # 功能组件
│
├── pages/
│   ├── auth/                  # 认证页面
│   ├── dashboard.tsx          # 仪表盘
│   └── ...
│
├── stores/
│   └── feature-store.ts       # Zustand状态
│
├── types/
│   └── feature.ts             # TypeScript类型
│
├── lib/
│   ├── api.ts                 # API客户端
│   └── utils.ts               # 工具函数
│
└── hooks/
    └── use-feature.ts         # 自定义Hook
```

## 3. 开发流程

### 3.1 功能开发流程

```
1. 创建分支
   git checkout -b feature/new-feature

2. 编写代码
   - 编写模型
   - 编写Schema
   - 编写API
   - 编写测试

3. 本地测试
   pytest -v
   npm test

4. 提交代码
   git add .
   git commit -m "feat: add new feature"

5. 推送分支
   git push origin feature/new-feature

6. 创建PR
   - 填写PR描述
   - 关联Issue
   - 请求Review

7. Code Review
   - 至少1人Approve
   - 解决Review意见

8. 合并代码
   - Squash Merge
   - 删除分支
```

### 3.2 API 开发规范

#### 创建新资源 API

**Step 1: 定义模型**

```python
# models/resource.py
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4
from datetime import datetime

class Resource(SQLModel, table=True):
    __tablename__ = "resource"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    organization_id: UUID = Field(foreign_key="organization.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Step 2: 定义 Schema**

```python
# schemas/resource.py
from pydantic import BaseModel
from uuid import UUID

class ResourceCreate(BaseModel):
    name: str
    description: str | None = None

class ResourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ResourceResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True
```

**Step 3: 实现 API**

```python
# api/v1/resources.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.dependencies import require_org_role
from ipflow.models import User
from ipflow.schemas.resource import ResourceCreate, ResourceResponse
from ipflow.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["resources"])

@router.get("", response_model=list[ResourceResponse])
async def list_resources(
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取资源列表."""
    service = ResourceService(db)
    return await service.get_resources(current_user.organization_id)

@router.post("", response_model=ResourceResponse)
async def create_resource(
    data: ResourceCreate,
    current_user: User = Depends(require_org_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """创建资源."""
    service = ResourceService(db)
    return await service.create_resource(data, current_user.organization_id)
```

**Step 4: 编写测试**

```python
# tests/unit/test_resource_service.py
import pytest
from ipflow.services.resource_service import ResourceService

@pytest.mark.asyncio
async def test_create_resource(db_session):
    service = ResourceService(db_session)
    resource = await service.create_resource(
        ResourceCreate(name="Test"),
        organization_id=uuid4()
    )
    assert resource.name == "Test"
```

### 3.3 前端组件开发

#### 创建新组件

**Step 1: 定义类型**

```typescript
// types/resource.ts
export interface Resource {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
}

export interface CreateResourceData {
  name: string;
  description?: string;
}
```

**Step 2: 创建 Store**

```typescript
// stores/resource-store.ts
import { create } from 'zustand';
import api from '@/lib/api';
import type { Resource, CreateResourceData } from '@/types/resource';

interface ResourceState {
  resources: Resource[];
  isLoading: boolean;
  fetchResources: () => Promise<void>;
  createResource: (data: CreateResourceData) => Promise<void>;
}

export const useResourceStore = create<ResourceState>((set) => ({
  resources: [],
  isLoading: false,
  
  fetchResources: async () => {
    set({ isLoading: true });
    const response = await api.get('/resources');
    set({ resources: response.data, isLoading: false });
  },
  
  createResource: async (data) => {
    const response = await api.post('/resources', data);
    set((state) => ({
      resources: [...state.resources, response.data]
    }));
  }
}));
```

**Step 3: 创建组件**

```tsx
// components/resource/resource-list.tsx
import { useEffect } from 'react';
import { useResourceStore } from '@/stores/resource-store';

export function ResourceList() {
  const { resources, isLoading, fetchResources } = useResourceStore();
  
  useEffect(() => {
    fetchResources();
  }, [fetchResources]);
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <ul>
      {resources.map((resource) => (
        <li key={resource.id}>{resource.name}</li>
      ))}
    </ul>
  );
}
```

## 4. 测试指南

### 4.1 测试结构

```
tests/
├── unit/                      # 单元测试
│   ├── test_models/
│   ├── test_services/
│   └── test_utils/
├── integration/               # 集成测试
│   ├── test_auth_api.py
│   ├── test_project_api.py
│   └── ...
├── e2e/                       # 端到端测试
│   └── test_workflow.py
├── fixtures/                  # 测试数据
│   └── data.py
└── conftest.py               # Pytest配置
```

### 4.2 编写单元测试

```python
# tests/unit/test_services/test_code_processor.py
import pytest
from ipflow.services.copyright.code_processor import CodeProcessor

@pytest.fixture
def processor():
    return CodeProcessor()

@pytest.mark.asyncio
async def test_extract_pages(processor, sample_code_dir):
    # Arrange
    config = ExtractConfig(first_n_pages=30, last_n_pages=30)
    
    # Act
    result = await processor.extract_pages(sample_code_dir, config)
    
    # Assert
    assert len(result.pages) == 60
    assert result.total_lines > 0

@pytest.mark.asyncio
async def test_invalid_file_type(processor):
    with pytest.raises(InvalidFileTypeError):
        await processor.process_file("test.txt")
```

### 4.3 编写集成测试

```python
# tests/integration/test_project_api.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from ipflow.main import app
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    response = client.post("/api/v1/auth/login", json={
        "username": "test_user",
        "password": "test_pass"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_project(client, auth_headers):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "type": "software_copyright"},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
```

### 4.4 运行测试

```bash
# 运行所有测试
cd backend
pytest

# 运行特定测试
pytest tests/unit/test_code_processor.py

# 运行并生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行前端测试
cd frontend
pnpm lint

# 运行 E2E 测试
npm run test:e2e
```

## 5. 调试技巧

### 5.1 后端调试

```python
# 使用 pdb
import pdb; pdb.set_trace()

# 使用 ipdb (推荐)
import ipdb; ipdb.set_trace()

# 使用 VSCode 调试
# .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["ipflow.main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

### 5.2 前端调试

```typescript
// 使用 React DevTools
// Chrome 扩展安装 React Developer Tools

// 使用 Redux DevTools (Zustand 兼容)
// 启用 devtools
import { devtools } from 'zustand/middleware';

const useStore = create(
  devtools((set) => ({ ... }))
);

// VSCode 调试
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000",
      "webRoot": "${workspaceFolder}/frontend"
    }
  ]
}
```

### 5.3 日志调试

```python
# 后端日志
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message: %s", variable)
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

```typescript
// 前端日志
console.log('Debug:', data);
console.table(arrayData);
console.time('operation');
// ... code
console.timeEnd('operation');
```

## 6. 数据库迁移

### 6.1 创建迁移

```bash
cd backend

# 自动检测变更创建迁移
alembic revision --autogenerate -m "add user table"

# 手动创建迁移
alembic revision -m "add index"
```

### 6.2 编辑迁移脚本

```python
# migrations/versions/xxx_add_user_table.py
def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )

def downgrade():
    op.drop_table('user')
```

### 6.3 执行迁移

```bash
# 升级到最新
alembic upgrade head

# 升级到指定版本
alembic upgrade revision_id

# 回滚一次
alembic downgrade -1

# 回滚到指定版本
alembic downgrade revision_id

# 查看历史
alembic history

# 查看当前版本
alembic current
```

## 7. 性能优化

### 7.1 数据库优化

```python
# 添加索引
from sqlalchemy import Index

class Project(SQLModel, table=True):
    __tablename__ = "project"
    
    name: str = Field(index=True)
    status: str = Field(index=True)
    
    __table_args__ = (
        Index('idx_org_status', 'organization_id', 'status'),
    )

# 查询优化
from sqlalchemy.orm import selectinload

# 使用 joinedload 避免 N+1
result = await db.execute(
    select(Project)
    .options(selectinload(Project.owner))
    .where(Project.organization_id == org_id)
)
```

### 7.2 缓存优化

```python
from ipflow.core.cache import cache

@cache.cached(timeout=300, key_prefix="user")
async def get_user(user_id: UUID):
    return await db.get(User, user_id)

# 手动清除缓存
@cache.evict(key_prefix="user", args=["user_id"])
async def update_user(user_id: UUID, data: dict):
    ...
```

### 7.3 前端优化

```typescript
// 虚拟列表
import { VirtualList } from '@/components/ui/virtual-list';

// 代码分割
const LazyComponent = lazy(() => import('./HeavyComponent'));

// 缓存请求
const { data } = useSWR('/api/projects', fetcher, {
  revalidateOnFocus: false,
  dedupingInterval: 5000
});
```

## 8. 代码审查清单

### 8.1 后端审查项

- [ ] 代码符合 PEP 8 规范
- [ ] 类型注解完整
- [ ] 错误处理完善
- [ ] 单元测试覆盖
- [ ] API 文档更新
- [ ] 数据库迁移脚本
- [ ] 安全漏洞检查
- [ ] 性能考虑

### 8.2 前端审查项

- [ ] 代码符合 ESLint 规则
- [ ] TypeScript 类型完整
- [ ] 组件复用性
- [ ] 状态管理合理
- [ ] 错误边界处理
- [ ] 响应式设计
- [ ] 无障碍支持
- [ ] 性能优化

## 9. 发布流程

### 9.1 版本号规范

遵循 [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- MAJOR: 不兼容的API变更
- MINOR: 向下兼容的功能添加
- PATCH: 向下兼容的问题修复

### 9.2 发布步骤

```bash
# 1. 更新版本号
# pyproject.toml
# package.json

# 2. 更新 CHANGELOG.md

# 3. 创建发布分支
git checkout -b release/2.1.0

# 4. 执行测试
pytest
npm test

# 5. 合并到 main
git checkout main
git merge release/2.1.0

# 6. 打标签
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0

# 7. 部署
./scripts/deploy.sh production
```

## 10. 常见问题

### Q1: 数据库连接失败

```bash
# 检查 PostgreSQL 服务
sudo systemctl status postgresql

# 检查连接配置
cat .env | grep DATABASE_URL

# 测试连接
psql -h localhost -U ipflow -d ipflow
```

### Q2: 前端无法连接后端

```bash
# 检查 CORS 配置
# backend/src/ipflow/main.py

# 检查代理配置
# frontend/next.config.ts
```

### Q3: 迁移失败

```bash
# 查看当前版本
alembic current

# 手动修复
alembic downgrade -1
# 修复代码
alembic upgrade head
```

## 11. 参考资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Zustand 文档](https://docs.pmnd.rs/zustand)
- [Tailwind CSS 文档](https://tailwindcss.com/)
