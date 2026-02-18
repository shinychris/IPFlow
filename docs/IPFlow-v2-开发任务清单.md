# IPFlow v2.0 开发任务清单

> **项目目标**: 将 IPFlow 从原型升级为商业化级知识产权申请管理平台  
> **开发周期**: 预计 4-6 个月（2-3 名全职开发）  
> **最后更新**: 2026-02-17

---

## 项目里程碑规划

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              IPFlow v2.0 开发路线图                                   │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  月份    M1              M2              M3              M4              M5-M6      │
│          │               │               │               │               │          │
│  ────────┼───────────────┼───────────────┼───────────────┼───────────────┼────────  │
│          │               │               │               │               │          │
│  里程碑  ▼               ▼               ▼               ▼               ▼          │
│        ┌───┐          ┌───┐          ┌───┐          ┌───┐          ┌─────────┐      │
│        │M1 │─────────▶│M2 │─────────▶│M3 │─────────▶│M4 │─────────▶│   M5    │      │
│        └───┘          └───┘          └───┘          └───┘          └─────────┘      │
│          │               │               │               │               │          │
│  目标    │ 后端基础架构   │ 核心功能迁移   │ 前端重构升级   │ 商业化功能    │ 测试优化  │
│          │ + 用户认证     │ + 软著全流程   │ + 管理后台     │ + 付费系统    │ + 上线    │
│          │               │               │               │               │          │
│  交付    │ 可运行的      │ 功能对等的    │ 体验升级的    │ 可收费的     │ 生产就绪   │
│  物      │ Python后端    │ v2 软著系统   │ 全栈应用      │ 产品        │ 的产品    │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 第一阶段：后端基础架构搭建（M1：第1-4周）

### Week 1: 项目初始化与工具链

#### 任务 1.1: 初始化 Python 项目结构
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `backend/pyproject.toml` - uv 项目配置
  - [ ] `backend/README.md` - 开发文档
  - [ ] `backend/.env.example` - 环境变量模板
  - [ ] `backend/.gitignore`
  - [ ] `backend/.python-version` (3.12)

```toml
# pyproject.toml 关键配置示例
[project]
name = "ipflow"
version = "2.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlmodel>=0.0.22",
    "asyncpg>=0.30.0",
    "pydantic-settings>=2.7.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "redis>=5.2.0",
    "celery>=5.4.0",
    "minio>=7.2.0",
    "python-multipart>=0.0.20",
    "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "ruff>=0.9.0",
    "mypy>=1.14.0",
    "alembic>=1.14.0",
    "factory-boy>=3.3.0",
]
```

#### 任务 1.2: 配置开发工具链
- **优先级**: P0
- **预估工时**: 3h
- **交付物**:
  - [ ] `ruff` 代码格式化与检查配置
  - [ ] `mypy` 类型检查配置
  - [ ] `pytest` 测试配置
  - [ ] `alembic` 初始化
  - [ ] Git pre-commit hooks

#### 任务 1.3: Docker 开发环境
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `backend/Dockerfile`
  - [ ] `docker-compose.yml` (含 PostgreSQL 18, Redis, MinIO)
  - [ ] `backend/Dockerfile.dev` (热重载开发版)
  - [ ] `.dockerignore`

### Week 2: 核心基础设施

#### 任务 2.1: 配置管理系统
- **优先级**: P0
- **预估工时**: 3h
- **交付物**:
  - [ ] `src/ipflow/config.py` - Pydantic Settings
  - [ ] 环境变量验证
  - [ ] 不同环境配置分离 (dev/staging/prod)

```python
# 关键配置类
class Settings(BaseSettings):
    # 应用
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # 数据库
    DATABASE_URL: PostgresDsn
    
    # 安全
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: RedisDsn
    
    # 存储
    STORAGE_TYPE: str = "minio"
    STORAGE_ENDPOINT: str
    STORAGE_ACCESS_KEY: str
    STORAGE_SECRET_KEY: str
```

#### 任务 2.2: 日志与异常处理
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `src/ipflow/core/logging.py` - 结构化 JSON 日志
  - [ ] `src/ipflow/core/exceptions.py` - 自定义异常类
  - [ ] 全局异常处理中间件
  - [ ] 请求 ID 追踪

#### 任务 2.3: 数据库连接与会话管理
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `src/ipflow/db/session.py` - 异步 Session 管理
  - [ ] 数据库连接池配置
  - [ ] 依赖注入函数 `get_db()`

### Week 3: 认证与安全系统

#### 任务 3.1: JWT 认证实现
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] `src/ipflow/core/security.py`:
    - [ ] 密码哈希 (bcrypt)
    - [ ] JWT 令牌创建/验证
    - [ ] 刷新令牌管理
  - [ ] 令牌黑名单 (Redis)
  - [ ] 依赖注入: `get_current_user`, `get_current_active_user`

#### 任务 3.2: 认证 API 路由
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `src/ipflow/api/v1/auth.py`:
    - [ ] `POST /auth/register` - 注册
    - [ ] `POST /auth/login` - 登录
    - [ ] `POST /auth/logout` - 登出
    - [ ] `POST /auth/refresh` - 刷新令牌
    - [ ] `GET /auth/me` - 获取当前用户

#### 任务 3.3: 用户模型与 CRUD
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `src/ipflow/models/user.py` - User SQLModel
  - [ ] `src/ipflow/services/user_service.py`:
    - [ ] `create_user`
    - [ ] `get_by_id`
    - [ ] `get_by_email`
    - [ ] `update`
    - [ ] `delete` (软删除)

### Week 4: 测试与文档

#### 任务 4.1: 单元测试框架
- **优先级**: P1
- **预估工时**: 4h
- **交付物**:
  - [ ] `tests/conftest.py` - pytest 配置与 fixtures
  - [ ] `tests/unit/test_security.py` - 安全模块测试
  - [ ] `tests/unit/test_user_service.py` - 用户服务测试
  - [ ] 测试数据库配置 (SQLite in-memory 或 独立 PostgreSQL)

#### 任务 4.2: API 文档与测试
- **优先级**: P1
- **预估工时**: 3h
- **交付物**:
  - [ ] FastAPI 自动 OpenAPI 文档优化
  - [ ] `tests/integration/test_auth_api.py` - 认证 API 集成测试
  - [ ] API 测试覆盖率 > 80%

#### 任务 4.3: M1 里程碑验收
- **优先级**: P0
- **预估工时**: 2h
- **验收标准**:
  - [ ] `docker-compose up` 一键启动全部服务
  - [ ] 用户可注册、登录、获取个人信息
  - [ ] API 文档可访问 `/docs`
  - [ ] 所有测试通过

---

## 第二阶段：核心功能迁移（M2：第5-8周）

### Week 5: 项目基础模型与 CRUD

#### 任务 5.1: 项目模型设计
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `src/ipflow/models/project.py`:
    - [ ] `Project` 基础模型
    - [ ] `ProjectStatus` 枚举
    - [ ] `ProjectType` 枚举
  - [ ] Alembic 迁移脚本

#### 任务 5.2: 软著专用模型
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `src/ipflow/models/copyright.py`:
    - [ ] `CopyrightData` - 软著信息
    - [ ] `CodeBundle` - 代码包
    - [ ] `CopyrightManual` - 说明书
    - [ ] `ManualScreenshot` - 截图

#### 任务 5.3: 项目 API 路由
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] `src/ipflow/api/v1/projects.py`:
    - [ ] `GET /projects` - 项目列表（分页、筛选）
    - [ ] `POST /projects` - 创建项目
    - [ ] `GET /projects/{id}` - 项目详情
    - [ ] `PATCH /projects/{id}` - 更新项目
    - [ ] `DELETE /projects/{id}` - 删除项目
    - [ ] `POST /projects/{id}/duplicate` - 复制项目

### Week 6: 代码处理引擎

#### 任务 6.1: ZIP 文件处理服务
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] `src/ipflow/services/copyright/code_processor.py`:
    - [ ] 文件解压与扫描
    - [ ] 代码文件识别（40+ 语言）
    - [ ] 目录过滤（node_modules 等）
    - [ ] 行数统计与语言分析

#### 任务 6.2: 代码分页引擎
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] 代码合并逻辑
  - [ ] 前30页 + 后30页分页算法
  - [ ] 行号添加（5位对齐）
  - [ ] 代码不足时的填充策略

#### 任务 6.3: 文件上传 API
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `src/ipflow/api/v1/uploads.py`:
    - [ ] `POST /uploads` - 文件上传
    - [ ] MinIO 存储集成
    - [ ] 文件元数据记录
    - [ ] 大文件分片上传（预留）

### Week 7: 软著业务 API

#### 任务 7.1: 软著信息 API
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `src/ipflow/api/v1/copyright/software_info.py`:
    - [ ] `GET /copyright/projects/{id}/software-info`
    - [ ] `PUT /copyright/projects/{id}/software-info`

#### 任务 7.2: 代码包 API
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `src/ipflow/api/v1/copyright/code_bundles.py`:
    - [ ] `GET /copyright/projects/{id}/code-bundles`
    - [ ] `POST /copyright/projects/{id}/code-bundles` (上传并处理)
    - [ ] `DELETE /copyright/projects/{id}/code-bundles/{bid}`
    - [ ] `GET /copyright/projects/{id}/code-bundles/{bid}/preview`

#### 任务 7.3: 说明书 API
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `src/ipflow/api/v1/copyright/manuals.py`:
    - [ ] `GET /copyright/projects/{id}/manuals`
    - [ ] `POST /copyright/projects/{id}/manuals`
    - [ ] `PUT /copyright/projects/{id}/manuals/{mid}`
    - [ ] 模板类型枚举支持

### Week 8: 合规检查与导出

#### 任务 8.1: 合规检查服务
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `src/ipflow/services/copyright/compliance_checker.py`:
    - [ ] 软件信息检查
    - [ ] 代码页数检查
    - [ ] 说明书页数检查
    - [ ] 证明材料检查
  - [ ] 合规检查模型

#### 任务 8.2: 合规检查 API
- **优先级**: P0
- **预估工时**: 3h
- **交付物**:
  - [ ] `src/ipflow/api/v1/compliance.py`:
    - [ ] `GET /projects/{id}/compliance`
    - [ ] `POST /projects/{id}/compliance/check`

#### 任务 8.3: 导出包生成
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] `src/ipflow/services/copyright/export_generator.py`:
    - [ ] 材料清单生成
    - [ ] 源代码格式化文档
    - [ ] 说明书导出
    - [ ] 打印指南生成
    - [ ] 网报对照表生成
    - [ ] ZIP 打包
  - [ ] Celery 异步任务支持

#### 任务 8.4: M2 里程碑验收
- **优先级**: P0
- **预估工时**: 2h
- **验收标准**:
  - [ ] 可通过 API 完成完整的软著申请流程
  - [ ] 代码上传、处理、分页功能正常
  - [ ] 合规检查正确识别问题
  - [ ] 导出的 ZIP 包包含所有必需文件

---

## 第三阶段：前端重构（M3：第9-12周）

### Week 9: 前端基础重构

#### 任务 9.1: 状态管理升级
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `frontend/src/stores/auth-store.ts` - Zustand 认证状态
  - [ ] `frontend/src/stores/ui-store.ts` - UI 状态
  - [ ] `frontend/src/stores/project-store.ts` - 项目编辑状态
  - [ ] JWT 刷新令牌逻辑

#### 任务 9.2: API 客户端重构
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `frontend/src/api/client.ts` - Axios 封装
  - [ ] `frontend/src/api/auth.ts` - 认证 API
  - [ ] `frontend/src/api/projects.ts` - 项目 API
  - [ ] 请求/响应拦截器（错误处理、令牌刷新）

#### 任务 9.3: 类型定义同步
- **优先级**: P1
- **预估工时**: 3h
- **交付物**:
  - [ ] `frontend/src/types/api.ts` - API 类型（与后端 Pydantic 同步）
  - [ ] `frontend/src/types/models.ts` - 业务模型类型

### Week 10: 核心组件重构

#### 任务 10.1: 文件上传组件增强
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] `frontend/src/components/common/file-uploader/`:
    - [ ] 拖拽上传
    - [ ] 进度显示
    - [ ] 多文件支持
    - [ ] 错误重试

#### 任务 10.2: 代码预览组件
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `frontend/src/components/common/code-viewer/`:
    - [ ] 语法高亮 (Prism.js / highlight.js)
    - [ ] 行号显示
    - [ ] 分页浏览
    - [ ] 搜索功能

#### 任务 10.3: 富文本编辑器
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] 集成 TipTap / Plate.js
  - [ ] 图片上传
  - [ ] 模板插入
  - [ ] 字数/页数统计

### Week 11: 页面重构

#### 任务 11.1: 认证页面
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `frontend/src/pages/auth/login.tsx` - 新登录页
  - [ ] `frontend/src/pages/auth/register.tsx` - 新注册页
  - [ ] 表单校验 (react-hook-form + zod)

#### 任务 11.2: 工作台与项目列表
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `frontend/src/pages/dashboard/index.tsx` - 工作台（优化版）
  - [ ] `frontend/src/pages/projects/list.tsx` - 项目列表（数据表格）
  - [ ] 统计卡片组件

#### 任务 11.3: 软著向导页面
- **优先级**: P0
- **预估工时**: 8h
- **交付物**:
  - [ ] 向导框架重构
  - [ ] Step 1: 软件信息表单
  - [ ] Step 2: 代码上传与预览
  - [ ] Step 3: 说明书编辑
  - [ ] Step 4: 合规检查与导出

### Week 12: 前端优化与测试

#### 任务 12.1: UI/UX 优化
- **优先级**: P1
- **预估工时**: 5h
- **交付物**:
  - [ ] 骨架屏加载
  - [ ] 错误边界
  - [ ] 乐观更新
  - [ ] 响应式优化（移动端适配）

#### 任务 12.2: 前端测试
- **优先级**: P1
- **预估工时**: 4h
- **交付物**:
  - [ ] Vitest 单元测试配置
  - [ ] 组件测试（关键组件）
  - [ ] Playwright E2E 测试（关键流程）

#### 任务 12.3: M3 里程碑验收
- **优先级**: P0
- **预估工时**: 2h
- **验收标准**:
  - [ ] 前端可完整对接新后端 API
  - [ ] 软著申请流程用户体验流畅
  - [ ] 移动端可正常浏览

---

## 第四阶段：商业化功能（M4：第13-16周）

### Week 13: 组织与多租户

#### 任务 13.1: 组织模型
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `Organization` 模型
  - [ ] `OrganizationMember` 模型
  - [ ] 多租户上下文中间件

#### 任务 13.2: 组织管理 API
- **优先级**: P0
- **预估工时**: 5h
- **交付物**:
  - [ ] `GET/POST /organizations` - 组织列表/创建
  - [ ] `GET/PATCH /organizations/{id}` - 详情/更新
  - [ ] `GET/POST /organizations/{id}/members` - 成员管理
  - [ ] 邀请码系统（预留）

#### 任务 13.3: 前端组织切换
- **优先级**: P0
- **预估工时**: 3h
- **交付物**:
  - [ ] 组织选择器组件
  - [ ] 组织设置页面
  - [ ] 成员管理界面

### Week 14: 订阅与计费

#### 任务 14.1: 订阅系统模型
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] `Plan` 模型 - 订阅计划
  - [ ] `Subscription` 模型 - 订阅记录
  - [ ] `Invoice` 模型 - 发票
  - [ ] Alembic 迁移

#### 任务 14.2: 限额控制
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] 项目数量限制检查
  - [ ] 存储空间限制检查
  - [ ] 团队成员限制检查
  - [ ] 功能开关控制

#### 任务 14.3: 支付集成（预留）
- **优先级**: P1
- **预估工时**: 6h
- **交付物**:
  - [ ] Stripe / 支付宝 / 微信支付集成框架
  - [ ] Webhook 处理
  - [ ] 订阅状态同步

### Week 15: 管理后台

#### 任务 15.1: 后端管理 API
- **优先级**: P1
- **预估工时**: 5h
- **交付物**:
  - [ ] `src/ipflow/api/admin/` - 管理后台路由
  - [ ] 用户管理 API
  - [ ] 组织管理 API
  - [ ] 审计日志 API

#### 任务 15.2: 前端管理后台
- **优先级**: P1
- **预估工时**: 8h
- **交付物**:
  - [ ] `frontend/src/pages/admin/`:
    - [ ] 仪表盘（统计）
    - [ ] 用户管理
    - [ ] 组织管理
    - [ ] 审计日志查看

### Week 16: 审计与监控

#### 任务 16.1: 审计日志系统
- **优先级**: P1
- **预估工时**: 4h
- **交付物**:
  - [ ] `AuditLog` 模型
  - [ ] 审计日志中间件
  - [ ] 关键操作自动记录

#### 任务 16.2: 监控与告警
- **优先级**: P1
- **预估工时**: 4h
- **交付物**:
  - [ ] 应用指标暴露 (Prometheus)
  - [ ] 健康检查端点
  - [ ] 结构化日志收集

#### 任务 16.3: M4 里程碑验收
- **优先级**: P0
- **预估工时**: 2h
- **验收标准**:
  - [ ] 多租户数据隔离正常
  - [ ] 订阅计划功能可用
  - [ ] 管理后台可正常管理用户/组织
  - [ ] 审计日志记录完整

---

## 第五阶段：测试优化与上线（M5-M6：第17-24周）

### Week 17-18: 全面测试

#### 任务 17.1: 后端测试完善
- **优先级**: P0
- **预估工时**: 12h
- **交付物**:
  - [ ] 单元测试覆盖率 > 80%
  - [ ] 集成测试覆盖所有 API
  - [ ] 代码处理引擎边界测试
  - [ ] 性能测试（大文件上传）

#### 任务 17.2: 前端测试完善
- **优先级**: P0
- **预估工时**: 10h
- **交付物**:
  - [ ] 关键组件单元测试
  - [ ] 页面集成测试
  - [ ] E2E 测试覆盖完整流程

#### 任务 17.3: 安全审计
- **优先级**: P0
- **预估工时**: 8h
- **交付物**:
  - [ ] 依赖漏洞扫描
  - [ ] OWASP Top 10 检查
  - [ ] 认证/授权测试
  - [ ] 文件上传安全测试

### Week 19-20: 性能优化

#### 任务 19.1: 后端性能优化
- **优先级**: P1
- **预估工时**: 10h
- **交付物**:
  - [ ] 数据库查询优化
  - [ ] Redis 缓存策略
  - [ ] 大文件异步处理
  - [ ] API 响应时间优化

#### 任务 19.2: 前端性能优化
- **优先级**: P1
- **预估工时**: 8h
- **交付物**:
  - [ ] 代码分割
  - [ ] 图片/资源优化
  - [ ] 虚拟列表（大数据量）
  - [ ] Lighthouse 评分优化

### Week 21-22: 生产部署准备

#### 任务 21.1: 生产环境配置
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] 生产环境 Docker Compose
  - [ ] Kubernetes 部署配置（可选）
  - [ ] CI/CD 流水线完善
  - [ ] 环境变量管理

#### 任务 21.2: 备份与恢复
- **优先级**: P0
- **预估工时**: 4h
- **交付物**:
  - [ ] 数据库自动备份脚本
  - [ ] 文件存储备份策略
  - [ ] 灾难恢复文档

#### 任务 21.3: 运维文档
- **优先级**: P1
- **预估工时**: 4h
- **交付物**:
  - [ ] 部署手册
  - [ ] 监控告警配置
  - [ ] 故障排查指南

### Week 23-24: 上线与迭代

#### 任务 23.1: Beta 测试
- **优先级**: P0
- **预估工时**: 8h
- **交付物**:
  - [ ] Beta 版本部署
  - [ ] 内测用户邀请
  - [ ] 问题收集与修复

#### 任务 23.2: 生产上线
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] 生产环境部署
  - [ ] 域名配置
  - [ ] SSL 证书
  - [ ] CDN 配置

#### 任务 23.3: 数据迁移
- **优先级**: P0
- **预估工时**: 6h
- **交付物**:
  - [ ] v1 数据导出脚本
  - [ ] v2 数据导入脚本
  - [ ] 数据验证
  - [ ] 回滚方案

---

## 附录：任务优先级说明

### 优先级定义

| 优先级 | 含义 | 处理原则 |
|--------|------|---------|
| **P0** | 阻塞性 | 必须完成，否则里程碑无法达成 |
| **P1** | 重要 | 应该完成，影响质量但不阻塞 |
| **P2** | 优化 | 最好完成，可延后或裁剪 |
| **P3** | 未来 | 后续版本考虑 |

### 任务标签

```
[前端]  - 前端相关任务
[后端]  - 后端相关任务
[DB]    - 数据库相关
[DevOps]- 部署运维相关
[测试]  - 测试相关
[文档]  - 文档相关
```

---

## 快速参考：本周可执行任务

如果你是刚开始，建议按以下顺序执行第一周任务：

```bash
# Day 1-2: 项目初始化
cd /Users/chris/CodingZone/ProjectsBase/4-Web-Applications/IPFlow
mkdir backend
cd backend
uv init --python 3.12 .

# 编辑 pyproject.toml 添加依赖
# 创建基础目录结构
mkdir -p src/ipflow/{api/v1/{copyright,patents,trademarks},core,models,services,db,tasks,utils}
mkdir -p tests/{unit,integration}

# Day 3-4: Docker 环境
docker-compose up -d  # 启动 PostgreSQL, Redis, MinIO

# Day 5-7: 核心基础设施
# 配置管理、日志、数据库连接、基础模型
```

---

**下一步**: 确定当前优先级后，我可以立即开始实现 **第一阶段 Week 1** 的具体代码。
