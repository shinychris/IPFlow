# IPFlow 知识产权助手 - 产品说明文档

> **版本**: v2.0（按当前代码校准）  
> **日期**: 2026-03-20  
> **状态**: 已支持软著/专利/商标全链路基础流程，持续完善中

---

## 一、产品概述

### 1.1 产品定位

**IPFlow 知识产权助手**是一款面向中国知识产权申请场景的专业工具应用，帮助用户高效生成和管理软件著作权（软著）、专利、商标三类申请材料的数字化平台。

### 1.2 核心价值主张

| 维度 | 价值描述 |
|------|---------|
| **效率提升** | 通过向导化流程和模板化文档，降低申请准备时间成本 |
| **合规支持** | 内置代码材料分页、说明书页数与材料完整性检查 |
| **流程标准化** | 统一项目生命周期：创建、填写、校验、导出 |
| **组织协作** | 支持组织、成员、角色与订阅配额管理 |

### 1.3 目标用户

- **独立开发者** - 需要为个人项目申请软著/专利
- **科技企业** - 批量管理知识产权申请材料
- **知识产权代理机构** - 提升材料准备效率
- **高校科研团队** - 管理科研成果知识产权

---

## 二、功能模块

### 2.1 业务类型支持

```
┌─────────────────────────────────────────────────────────────┐
│                     IPFlow 业务架构                          │
├───────────────┬───────────────┬─────────────────────────────┤
│   软著申请    │   专利申请    │        商标申请             │
│  (Copyright)  │   (Patent)    │       (Trademark)           │
├───────────────┼───────────────┼─────────────────────────────┤
│ 5步向导流程   │ 5步向导流程   │      4步向导流程            │
├───────────────┼───────────────┼─────────────────────────────┤
│ 1. 创建项目   │ 1. 创建项目   │      1. 创建项目            │
│ 2. 软件信息   │ 2. 专利信息   │      2. 商标信息            │
│ 3. 代码材料   │ 3. 权利要求   │      3. 商品服务分类        │
│ 4. 文档材料   │ 4. 说明书     │      4. 导出交付            │
│ 5. 导出交付   │ 5. 导出交付   │                             │
└───────────────┴───────────────┴─────────────────────────────┘
```

### 2.2 软著申请功能（代码已实现）

- **代码自动处理**: ZIP 解压、代码文件识别、前30页+后30页分页、行号与页眉添加
- **操作说明书**: 模板类型（web/mobile/algorithm/script/desktop）与内容保存
- **合规检查**: 软件信息、代码行数/页数、说明书页数等规则检查
- **导出交付**: 生成 ZIP 导出包（当前以 TXT 材料为主）

### 2.3 专利申请功能（代码已实现）

- 支持发明、实用新型、外观设计三类
- 专利信息、权利要求、说明书相关接口
- 导出接口已实现（说明书/权利要求/摘要/材料清单）

### 2.4 商标申请功能（代码已实现）

- 支持文字、图形、组合、三维、声音、颜色六种类型
- 商标信息与尼斯分类接口
- 导出接口已实现（申请书/分类清单/材料清单）

### 2.5 平台能力（代码已实现）

- 用户认证（JWT 访问令牌 + 刷新令牌）
- 组织与成员管理（邀请、角色、加入组织）
- 订阅与计费接口（计划、当前订阅、发票、用量、webhook）
- 管理后台接口（仪表盘、用户/组织/计划、审计日志）

---

## 三、技术架构（按当前仓库）

### 3.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **前端** | Next.js 16 + React 19 + TypeScript | App Router 架构 |
| **状态管理** | TanStack Query + Zustand | 服务端状态 + 本地状态 |
| **UI 框架** | shadcn/ui + Radix UI + Tailwind CSS | 组件化设计体系 |
| **后端** | FastAPI + SQLModel + Pydantic v2 | Python 3.12+ |
| **数据库** | PostgreSQL + Alembic | 关系数据与迁移 |
| **缓存/队列** | Redis + Celery | 会话/异步任务预留 |
| **对象存储** | MinIO（S3 兼容） | 文件上传与下载 |

### 3.2 项目结构

```
IPFlow/
├── backend/
│   ├── src/ipflow/
│   │   ├── api/v1/                  # FastAPI 路由
│   │   ├── models/                  # SQLModel 模型
│   │   ├── services/                # 业务服务（代码处理、合规等）
│   │   ├── core/                    # 安全/中间件/日志/监控
│   │   └── main.py                  # 应用入口
│   ├── alembic/                     # 数据库迁移
│   └── pyproject.toml
├── frontend/
│   ├── app/                         # Next.js App Router
│   ├── components/                  # 页面与 UI 组件
│   ├── api/                         # 前端 API 客户端
│   ├── stores/                      # Zustand store
│   └── lib/
├── shared/                          # 前后端共享类型
└── docs/
```

### 3.3 核心数据模型（摘要）

- **用户域**: `User`
- **项目域**: `Project`（含 `owner_id`、`project_type`、`status`、`current_step`）
- **软著域**: `CopyrightData`、`CodeBundle`、`CopyrightManual`
- **专利域**: `PatentData`、`PatentClaim`、`PatentDrawing`
- **商标域**: `TrademarkData`、`TrademarkNiceClass`、`NiceClassification`
- **组织与计费**: `Organization`、`OrganizationMember`、`Subscription`、`Plan`、`Invoice`
- **审计**: `AuditLog`

---

## 四、核心能力实现（代码现状）

### 4.1 代码处理引擎（软著）

位置：`backend/src/ipflow/services/copyright/code_processor.py`

- 支持多语言代码扩展名识别（40+）
- 自动忽略 `node_modules`、`.git`、`__pycache__` 等目录
- 按路径排序合并代码，分页输出
- 软著规则：优先生成前30页+后30页，每页50行，附行号与页眉
- 低于 3000 行时给出警告

### 4.2 合规检查（软著）

位置：`backend/src/ipflow/services/copyright/compliance_checker.py`

- 信息类：软件名、版本号、开发语言、功能描述、技术特点
- 代码类：总行数、文件数、页数
- 说明书类：标题、页数、字数、目录、章节结构
- 输出整体状态（passed/warning/failed）与是否可导出

### 4.3 导出能力（三业务）

- 软著导出：`backend/src/ipflow/api/v1/copyright/export.py`
- 专利导出：`backend/src/ipflow/api/v1/patents/export.py`
- 商标导出：`backend/src/ipflow/api/v1/trademarks/export.py`

说明：
- 三类业务均已提供导出接口和预览接口
- 当前导出内容主要为 ZIP + TXT 材料，PDF 规范化输出仍属于后续优化项

---

## 五、部署与运维（按当前工程脚本）

### 5.1 环境要求

- Python 3.12+
- Node.js + pnpm
- PostgreSQL 15+
- Redis 7+
- MinIO（可选但推荐）

### 5.2 常用命令

```bash
# 根目录安装依赖
make install

# 启动开发（前后端）
make dev

# 仅后端
make dev-backend

# 仅前端
make dev-frontend

# 测试与质量检查
make test
make lint
```

### 5.3 后端与前端单独命令

```bash
# 后端
cd backend
alembic upgrade head
pytest -v

# 前端
cd frontend
pnpm dev
pnpm lint
pnpm check
```

---

## 六、知识产权与安全

### 6.1 开源组件（主要）

- FastAPI
- SQLModel
- Next.js
- React
- shadcn/ui
- Tailwind CSS

### 6.2 安全能力（代码层）

- 密码哈希存储（bcrypt）
- JWT 访问令牌 + 刷新令牌
- 基于用户与角色的鉴权依赖
- 项目查询按 `owner_id` 做数据隔离
- 组织内角色控制（成员/管理员/超级管理员）

---

## 七、API 文档概要（当前路由）

Base URL: `/api/v1`

| 模块 | 示例端点 |
|------|---------|
| 认证 | `POST /auth/register` `POST /auth/login` `GET /auth/me` |
| 项目 | `GET /projects` `POST /projects` `PATCH /projects/{id}` |
| 软著 | `GET /copyright/projects/{id}/software-info` `POST /copyright/projects/{id}/export` |
| 专利 | `GET /patents/projects/{id}/patent-info` `POST /patents/projects/{id}/export` |
| 商标 | `GET /trademarks/projects/{id}/trademark-info` `POST /trademarks/projects/{id}/export` |
| 合规 | `GET /compliance/projects/{id}` `POST /compliance/projects/{id}/check` |
| 组织 | `GET /organizations` `POST /organizations/{id}/invite` |
| 订阅 | `GET /subscriptions/plans` `GET /subscriptions/current` |
| 管理后台 | `GET /admin/dashboard` `GET /admin/audit-logs` |

> 完整接口请以 `docs/API_ENDPOINTS.md` 与后端 OpenAPI (`/docs`) 为准。

---

## 八、当前实现状态（按代码扫描）

| 模块 | 状态 | 说明 |
|------|------|------|
| 用户认证系统 | ✅ 已实现 | 注册/登录/刷新/当前用户 |
| 项目管理 | ✅ 已实现 | CRUD + 复制 |
| 软著申请流程 | ✅ 已实现 | 5步流程、代码处理、合规检查、导出 |
| 专利申请流程 | ✅ 已实现 | 信息/权利要求/说明书/导出接口 |
| 商标申请流程 | ✅ 已实现 | 信息/尼斯分类/导出接口 |
| 组织协作 | ✅ 已实现 | 组织与成员管理、邀请加入 |
| 订阅计费 | ✅ 已实现 | 计划/订阅/发票/用量/webhook |
| 管理后台 | ✅ 已实现 | 统计、用户组织计划管理、审计日志 |
| PDF 正式材料导出 | 🟡 待增强 | 当前导出以 TXT 为主 |

---

## 九、说明

- 本文档已根据当前仓库代码结构与主要路由重新校准，替换了旧版 Node/Express/Wouter 描述。
- 若后续接口或模型发生调整，请同步更新 `docs/API_ENDPOINTS.md` 与本文档。
