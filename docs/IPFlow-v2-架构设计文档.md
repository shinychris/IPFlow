# IPFlow v2.0 架构设计文档

> **版本**: v2.0  
> **日期**: 2026年2月  
> **目标**: 知识产权申报材料辅助工具

---

## 一、技术栈重构总览

### 1.1 新旧技术栈对比

| 层级 | 当前技术栈 | 新技术栈 | 迁移原因 |
|------|-----------|---------|---------|
| **运行时** | Node.js 20+ | Python 3.12+ | Python 在数据处理/AI 集成方面生态更丰富 |
| **Web 框架** | Express 4.x | FastAPI 0.115+ | 原生异步支持、自动 API 文档、类型安全 |
| **数据库 ORM** | Drizzle ORM | SQLModel 0.22+ | 基于 SQLAlchemy 2.0 + Pydantic v2，类型一致性 |
| **数据校验** | Zod | Pydantic v2 | Python 生态标准，性能提升 5-50x |
| **包管理** | npm | uv 0.5+ | 极速依赖解析、内置虚拟环境、Python 新标准 |
| **认证** | express-session | JWT + Redis | 无状态、易扩展、支持分布式 |
| **任务队列** | 无 | Celery + Redis | 异步任务、定时任务、水平扩展 |
| **文件存储** | Replit Object Storage | MinIO / S3 | 云厂商无关、私有化部署友好 |

### 1.2 核心技术选型理由

#### FastAPI
- **异步优先**: 基于 Starlette + asyncio，处理文件上传/导出更高效
- **自动文档**: 自动生成 OpenAPI/Swagger UI，前后端协作效率提升
- **类型安全**: 全链路类型提示，减少运行时错误
- **生态丰富**: 与 Pydantic、SQLModel、Celery 无缝集成

#### SQLModel
- **统一模型**: 一个模型同时用于 ORM 和 API 序列化
- **基于 SQLAlchemy 2.0**: 成熟稳定，支持 PostgreSQL 18+ 新特性
- **类型推导**: 完整的类型提示，IDE 体验极佳

#### uv
- **极速**: Rust 编写，比 pip 快 10-100 倍
- **统一工具**: 替代 pip + virtualenv + pip-tools
- **PEP 合规**: 完全兼容 Python 标准

---

## 二、后端架构设计

### 2.1 项目结构

```
backend/                          # Python 后端根目录
├── pyproject.toml               # uv 项目配置 + 依赖管理
├── uv.lock                      # 锁定依赖版本
├── README.md
├── .env.example                 # 环境变量模板
├── .env                         # 本地环境变量（gitignore）
│
├── alembic/                     # 数据库迁移
│   ├── versions/                # 迁移脚本
│   ├── env.py
│   └── alembic.ini
│
├── src/
│   └── ipflow/                  # 主包
│       ├── __init__.py
│       ├── main.py              # FastAPI 应用入口
│       ├── config.py            # 配置管理（Pydantic Settings）
│       │
│       ├── api/                 # API 路由层
│       │   ├── __init__.py
│       │   ├── deps.py          # 依赖注入（认证、数据库等）
│       │   ├── v1/              # API v1
│       │   │   ├── __init__.py
│       │   │   ├── auth.py      # 认证相关
│       │   │   ├── users.py     # 用户管理
│       │   │   ├── projects.py  # 项目管理
│       │   │   ├── copyright/   # 软著模块
│       │   │   │   ├── __init__.py
│       │   │   │   ├── software_info.py
│       │   │   │   ├── code_bundles.py
│       │   │   │   ├── manuals.py
│       │   │   │   └── export.py
│       │   │   ├── patents/     # 专利模块
│       │   │   ├── trademarks/  # 商标模块
│       │   │   ├── uploads.py   # 文件上传
│       │   │   └── compliance.py # 合规检查
│       │   └── router.py        # 路由聚合
│       │
│       ├── core/                # 核心基础设施
│       │   ├── __init__.py
│       │   ├── security.py      # JWT、密码哈希
│       │   ├── exceptions.py    # 自定义异常
│       │   ├── logging.py       # 结构化日志
│       │   └── events.py        # 生命周期事件
│       │
│       ├── models/              # SQLModel 模型层
│       │   ├── __init__.py
│       │   ├── base.py          # 基础模型、Mixin
│       │   ├── user.py          # 用户模型
│       │   ├── project.py       # 项目基础模型
│       │   ├── copyright.py     # 软著相关模型
│       │   ├── patent.py        # 专利相关模型
│       │   ├── trademark.py     # 商标相关模型
│       │   └── enums.py         # 枚举定义
│       │
│       ├── schemas/             # Pydantic Schema（如需单独定义）
│       │   ├── __init__.py
│       │   ├── common.py        # 通用 Schema
│       │   ├── auth.py          # 认证相关
│       │   └── responses.py     # 统一响应格式
│       │
│       ├── services/            # 业务逻辑层
│       │   ├── __init__.py
│       │   ├── user_service.py
│       │   ├── project_service.py
│       │   ├── copyright/
│       │   │   ├── code_processor.py    # 代码处理引擎
│       │   │   ├── export_generator.py  # 导出包生成
│       │   │   └── compliance_checker.py # 合规检查
│       │   ├── storage_service.py       # 文件存储服务
│       │   └── ai_service.py            # AI 辅助服务（预留）
│       │
│       ├── db/                  # 数据库相关
│       │   ├── __init__.py
│       │   ├── session.py       # 异步 Session 管理
│       │   └── migrations/      # 迁移脚本（由 alembic 生成）
│       │
│       ├── tasks/               # Celery 异步任务
│       │   ├── __init__.py
│       │   ├── celery_app.py    # Celery 配置
│       │   ├── export_tasks.py  # 导出相关任务
│       │   └── notification_tasks.py # 通知任务
│       │
│       ├── utils/               # 工具函数
│       │   ├── __init__.py
│       │   ├── validators.py    # 自定义校验器
│       │   ├── file_utils.py    # 文件处理工具
│       │   └── pdf_generator.py # PDF 生成（将来）
│       │
│       └── templates/           # 模板文件
│           ├── manuals/         # 说明书模板
│           └── exports/         # 导出包模板
│
├── tests/                       # 测试
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── e2e/                     # 端到端测试
│
└── scripts/                     # 运维脚本
    ├── migrate.sh               # 数据库迁移
    ├── seed.py                  # 数据种子
    └── health_check.py          # 健康检查
```

### 2.2 技术架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              客户端层                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Web App    │  │  Mobile App  │  │   Admin      │                      │
│  │  (React 18)  │  │   (Future)   │  │   Dashboard  │                      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
└─────────┼─────────────────┼─────────────────┼──────────────────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ HTTPS / HTTP2
┌───────────────────────────┼─────────────────────────────────────────────────┐
│                           ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        负载均衡 / CDN                                │   │
│  │                     (Nginx / CloudFlare)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                           ┌────────┴────────┐                              │
│                           ▼                 ▼                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Application                             │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │   Auth      │ │  Projects   │ │   Uploads   │ │ Compliance  │   │   │
│  │  │   Router    │ │   Router    │ │   Router    │ │   Router    │   │   │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘   │   │
│  │         └───────────────┴───────────────┴───────────────┘          │   │
│  │                              │                                      │   │
│  │  ┌───────────────────────────┴─────────────────────────────────┐   │   │
│  │  │                   Services Layer (Business Logic)            │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │   │
│  │  │  │ Project  │ │ Copyright│ │ Patent   │ │ Trademark│       │   │   │
│  │  │  │ Service  │ │ Service  │ │ Service  │ │ Service  │       │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │   │
│  │  └────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┼─────────────────────────────────────┐ │
│  │                      数据层      │                                      │ │
│  │  ┌──────────────────────────────┼─────────────────────────────────┐   │ │
│  │  │         PostgreSQL 18+       │                                 │   │ │
│  │  │  ┌─────────┐ ┌─────────┐    │    ┌─────────┐ ┌─────────┐      │   │ │
│  │  │  │  Users  │ │ Projects│◄───┼───►│Copyright│ │ Patents │      │   │ │
│  │  │  └─────────┘ └─────────┘    │    └─────────┘ └─────────┘      │   │ │
│  │  └──────────────────────────────┘                                 │   │ │
│  │                                 │                                  │   │ │
│  │  ┌──────────────────────────────┼─────────────────────────────┐   │   │ │
│  │  │           Redis Cluster      │                             │   │   │ │
│  │  │  ┌──────────┐ ┌──────────────┼──┐ ┌──────────┐              │   │   │ │
│  │  │  │  Cache   │ │   Session    │  │ │  Celery  │              │   │   │ │
│  │  │  │  Store   │ │   Store      │  │ │  Broker  │              │   │   │ │
│  │  │  └──────────┘ └──────────────┘  │ └──────────┘              │   │   │ │
│  │  └─────────────────────────────────┘                             │   │ │
│  │                                                                    │   │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │ │
│  │  │              Object Storage (MinIO / S3)                   │   │   │ │
│  │  │     ┌──────────────┐    ┌──────────────┐                  │   │   │ │
│  │  │     │ Code Uploads │    │ Export Files │                  │   │   │ │
│  │  │     └──────────────┘    └──────────────┘                  │   │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │   │ │
│  └────────────────────────────────────────────────────────────────────┘   │ │
│                                                                            │ │
│  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│  │                    Celery Workers (Async Tasks)                    │   │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │ │
│  │  │ PDF Export   │ │ Code Process │ │ Notification │              │   │ │
│  │  │ Generation   │ │ Large Files  │ │ Email/SMS    │              │   │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘              │   │ │
│  └─────────────────────────────────────────────────────────────────────┘   │ │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、数据库模型设计（SQLModel）

### 3.1 基础设计原则

1. **统一时间戳**: 所有模型继承 `TimestampMixin`
2. **软删除**: 商业系统必备，使用 `deleted_at` 字段
3. **租户隔离**: 支持多租户，预留 `organization_id` 字段
4. **审计日志**: 关键表记录 `created_by`, `updated_by`
5. **UUID 主键**: 所有表使用 UUID v4 作为主键

### 3.2 核心模型定义

```python
# models/base.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime, String, event


class TimestampMixin(SQLModel):
    """时间戳混入类"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))


class AuditMixin(SQLModel):
    """审计混入类"""
    created_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    updated_by: Optional[UUID] = Field(default=None, foreign_key="user.id")


class BaseUUIDModel(SQLModel):
    """UUID 基础模型"""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
```

### 3.3 用户与权限模型

```python
# models/user.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column, String, Boolean
from pydantic import EmailStr

from .base import BaseUUIDModel, TimestampMixin, AuditMixin


class UserRole(str, Enum):
    """用户角色"""
    SUPER_ADMIN = "super_admin"      # 超级管理员
    ADMIN = "admin"                   # 组织管理员
    MANAGER = "manager"               # 项目经理
    MEMBER = "member"                 # 普通成员
    VIEWER = "viewer"                 # 只读用户


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseUUIDModel, TimestampMixin, table=True):
    """用户模型"""
    __tablename__ = "user"
    
    # 基本信息
    email: EmailStr = Field(sa_column=Column(String(255), unique=True, index=True))
    username: str = Field(sa_column=Column(String(50), unique=True, index=True))
    hashed_password: str = Field(sa_column=Column(String(255)))
    
    # 个人资料
    display_name: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    avatar_url: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None, sa_column=Column(String(20)))
    
    # 状态与角色
    role: UserRole = Field(default=UserRole.MEMBER)
    status: UserStatus = Field(default=UserStatus.PENDING)
    is_verified: bool = Field(default=False)
    
    # 安全
    last_login_at: Optional[datetime] = Field(default=None)
    last_login_ip: Optional[str] = Field(default=None, sa_column=Column(String(45)))
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    
    # 2FA（可选配套扩展）
    mfa_enabled: bool = Field(default=False)
    mfa_secret: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    
    # 关系
    organizations: List["OrganizationMember"] = Relationship(back_populates="user")
    projects: List["Project"] = Relationship(back_populates="owner")
    sessions: List["UserSession"] = Relationship(back_populates="user")
    
    # 元数据
    preferences: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class Organization(BaseUUIDModel, TimestampMixin, table=True):
    """组织/企业模型（多租户核心）"""
    __tablename__ = "organization"
    
    name: str = Field(sa_column=Column(String(100)))
    slug: str = Field(sa_column=Column(String(50), unique=True, index=True))
    description: Optional[str] = Field(default=None)
    
    # 商业信息
    business_type: Optional[str] = Field(default=None)  # 企业、个人、事务所
    license_number: Optional[str] = Field(default=None)  # 营业执照号
    contact_email: Optional[str] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None)
    
    # 订阅与限额
    plan_type: str = Field(default="free")  # free, pro, enterprise
    plan_expires_at: Optional[datetime] = Field(default=None)
    max_projects: int = Field(default=10)
    max_storage_bytes: int = Field(default=1073741824)  # 1GB
    used_storage_bytes: int = Field(default=0)
    
    # 状态
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    
    # 关系
    members: List["OrganizationMember"] = Relationship(back_populates="organization")
    projects: List["Project"] = Relationship(back_populates="organization")


class OrganizationMember(BaseUUIDModel, TimestampMixin, table=True):
    """组织成员关系模型"""
    __tablename__ = "organization_member"
    
    organization_id: UUID = Field(foreign_key="organization.id")
    user_id: UUID = Field(foreign_key="user.id")
    role: UserRole = Field(default=UserRole.MEMBER)
    
    # 加入时间
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关系
    organization: Organization = Relationship(back_populates="members")
    user: User = Relationship(back_populates="organizations")


class UserSession(BaseUUIDModel, TimestampMixin, table=True):
    """用户会话模型（JWT 黑名单/刷新令牌管理）"""
    __tablename__ = "user_session"
    
    user_id: UUID = Field(foreign_key="user.id")
    refresh_token: str = Field(sa_column=Column(String(500), index=True))
    expires_at: datetime = Field()
    
    # 设备信息
    device_id: Optional[str] = Field(default=None)  # 设备指纹
    device_name: Optional[str] = Field(default=None)
    device_type: Optional[str] = Field(default=None)  # web, mobile, desktop
    ip_address: Optional[str] = Field(default=None, sa_column=Column(String(45)))
    user_agent: Optional[str] = Field(default=None)
    
    # 状态
    is_active: bool = Field(default=True)
    last_used_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关系
    user: User = Relationship(back_populates="sessions")


class AuditLog(BaseUUIDModel, TimestampMixin, table=True):
    """审计日志（关键操作记录）"""
    __tablename__ = "audit_log"
    
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    
    # 操作信息
    action: str = Field(sa_column=Column(String(50), index=True))  # create, update, delete, export, etc.
    resource_type: str = Field(sa_column=Column(String(50)))  # project, code_bundle, etc.
    resource_id: Optional[UUID] = Field(default=None)
    
    # 详情
    old_values: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    new_values: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 上下文
    ip_address: Optional[str] = Field(default=None, sa_column=Column(String(45)))
    user_agent: Optional[str] = Field(default=None)
    request_id: Optional[str] = Field(default=None, sa_column=Column(String(100)))
```

### 3.4 项目模型（软著/专利/商标统一架构）

```python
# models/project.py
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column, String, Integer, Text, Date, ForeignKey
from sqlalchemy import JSON

from .base import BaseUUIDModel, TimestampMixin, AuditMixin


class ProjectType(str, Enum):
    """项目类型"""
    COPYRIGHT = "copyright"       # 软件著作权
    PATENT = "patent"             # 专利
    TRADEMARK = "trademark"       # 商标


class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"               # 草稿
    IN_PROGRESS = "in_progress"   # 进行中
    REVIEWING = "reviewing"       # 审核中
    PENDING_SUBMIT = "pending_submit"  # 待提交
    SUBMITTED = "submitted"       # 已提交
    ACCEPTED = "accepted"         # 已受理
    APPROVED = "approved"         # 已通过
    REJECTED = "rejected"         # 被驳回
    WITHDRAWN = "withdrawn"       # 已撤回


class SubjectType(str, Enum):
    """主体类型"""
    INDIVIDUAL = "individual"         # 个人
    ENTERPRISE = "enterprise"         # 企业
    INSTITUTION = "institution"       # 高校/研究机构
    AGENCY = "agency"                 # 代理机构


class Project(BaseUUIDModel, TimestampMixin, AuditMixin, table=True):
    """项目基础模型"""
    __tablename__ = "project"
    
    # 归属
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    owner_id: UUID = Field(foreign_key="user.id")
    
    # 类型与状态
    project_type: ProjectType
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT)
    current_step: int = Field(default=1)
    
    # 基本信息
    name: str = Field(sa_column=Column(String(100)))
    version: str = Field(default="V1.0", sa_column=Column(String(20)))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # 申请主体信息（冗余设计，方便查询）
    subject_type: SubjectType
    subject_name: Optional[str] = Field(default=None, sa_column=Column(String(100)))  # 权利人名称
    subject_id_number: Optional[str] = Field(default=None, sa_column=Column(String(50)))  # 证件号
    
    # 开发信息（软著专用，其他类型可为空）
    development_method: Optional[str] = Field(default=None)  # independent, cooperative, etc.
    publication_status: Optional[str] = Field(default=None)  # published, unpublished
    completion_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    first_publication_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    
    # 标签和元数据
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 外部系统对接
    external_system_id: Optional[str] = Field(default=None)  # 版权中心申请号等
    external_status: Optional[str] = Field(default=None)
    external_updated_at: Optional[datetime] = Field(default=None)
    
    # 完成度评分（AI辅助）
    completeness_score: Optional[int] = Field(default=None)  # 0-100
    
    # 关系
    organization: Optional[Organization] = Relationship(back_populates="projects")
    owner: User = Relationship(back_populates="projects")
    
    # 类型特定数据（一对一关系）
    copyright_data: Optional["CopyrightData"] = Relationship(back_populates="project")
    patent_data: Optional["PatentData"] = Relationship(back_populates="project")
    trademark_data: Optional["TrademarkData"] = Relationship(back_populates="project")
    
    # 通用关联
    uploads: List["FileUpload"] = Relationship(back_populates="project")
    compliance_checks: List["ComplianceCheck"] = Relationship(back_populates="project")
    export_packages: List["ExportPackage"] = Relationship(back_populates="project")
    activities: List["ProjectActivity"] = Relationship(back_populates="project")


class ProjectActivity(BaseUUIDModel, TimestampMixin, table=True):
    """项目活动日志（时间线）"""
    __tablename__ = "project_activity"
    
    project_id: UUID = Field(foreign_key="project.id")
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    activity_type: str = Field(sa_column=Column(String(50)))  # step_complete, file_upload, export, etc.
    title: str = Field(sa_column=Column(String(100)))
    description: Optional[str] = Field(default=None)
    
    # 关联数据
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 关系
    project: Project = Relationship(back_populates="activities")


class FileUpload(BaseUUIDModel, TimestampMixin, table=True):
    """文件上传记录"""
    __tablename__ = "file_upload"
    
    project_id: UUID = Field(foreign_key="project.id")
    uploaded_by: UUID = Field(foreign_key="user.id")
    
    # 文件信息
    original_name: str = Field(sa_column=Column(String(255)))
    storage_name: str = Field(sa_column=Column(String(255)))  # 存储文件名（UUID）
    storage_path: str = Field(sa_column=Column(String(500)))
    file_size: int = Field(sa_column=Column(Integer))  # bytes
    mime_type: str = Field(sa_column=Column(String(100)))
    checksum: str = Field(sa_column=Column(String(64)))  # SHA-256
    
    # 分类
    file_category: str = Field(sa_column=Column(String(50)))  # code, proof, manual, drawing
    file_type: str = Field(sa_column=Column(String(50)))  # identity, contract, trademark_image, etc.
    
    # 处理状态
    processing_status: str = Field(default="pending")  # pending, processing, completed, failed
    processing_result: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 关系
    project: Project = Relationship(back_populates="uploads")
```

### 3.5 软著专用模型

```python
# models/copyright.py
from typing import Optional, List
from uuid import UUID
from sqlmodel import Field, SQLModel, Relationship, Column, String, Integer, Text, ForeignKey
from sqlalchemy import JSON

from .base import BaseUUIDModel, TimestampMixin


class CopyrightData(BaseUUIDModel, TimestampMixin, table=True):
    """软著项目详细信息"""
    __tablename__ = "copyright_data"
    
    project_id: UUID = Field(foreign_key="project.id", unique=True)
    
    # 软件基本信息
    software_full_name: str = Field(sa_column=Column(String(100)))
    software_short_name: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    version_number: str = Field(sa_column=Column(String(20)))
    
    # 技术信息
    development_language: str = Field(sa_column=Column(String(100)))  # 支持多种语言
    development_environment: Optional[str] = Field(default=None, sa_column=Column(Text))
    runtime_environment: Optional[str] = Field(default=None, sa_column=Column(Text))
    code_line_count: Optional[int] = Field(default=None)
    
    # 功能描述
    functional_description: Optional[str] = Field(default=None, sa_column=Column(Text))
    technical_features: Optional[str] = Field(default=None, sa_column=Column(Text))
    target_domain: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    
    # 关系
    project: Project = Relationship(back_populates="copyright_data")
    code_bundles: List["CodeBundle"] = Relationship(back_populates="copyright_data")
    manuals: List["CopyrightManual"] = Relationship(back_populates="copyright_data")


class CodeBundle(BaseUUIDModel, TimestampMixin, table=True):
    """代码包（处理后的源代码）"""
    __tablename__ = "code_bundle"
    
    copyright_data_id: UUID = Field(foreign_key="copyright_data.id")
    upload_id: Optional[UUID] = Field(default=None, foreign_key="file_upload.id")
    
    # 原始文件信息
    original_file_name: str = Field(sa_column=Column(String(255)))
    original_file_size: int = Field()
    
    # 处理结果
    total_files: int = Field()
    total_lines: int = Field()
    processed_lines: int = Field()  # 实际用于生成文档的行数
    
    # 代码页数据（存储结构化数据）
    pages_data: List[dict] = Field(sa_column=Column(JSON))  # [{page_number, content, line_start, line_end, section}]
    
    # 文件类型统计
    language_stats: dict = Field(sa_column=Column(JSON))  # {".py": 1500, ".js": 800}
    
    # 合规状态
    has_enough_code: bool = Field(default=False)  # 是否有足够代码（3000+行）
    warnings: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # 存储路径
    processed_file_path: Optional[str] = Field(default=None)  # 处理后的文件存储路径
    
    # 关系
    copyright_data: CopyrightData = Relationship(back_populates="code_bundles")


class CopyrightManual(BaseUUIDModel, TimestampMixin, table=True):
    """软著操作说明书"""
    __tablename__ = "copyright_manual"
    
    copyright_data_id: UUID = Field(foreign_key="copyright_data.id")
    
    # 模板信息
    template_type: str = Field(sa_column=Column(String(20)))  # web, mobile, algorithm, script, desktop
    
    # 内容（富文本/HTML）
    title: str = Field(default="软件操作说明书", sa_column=Column(String(100)))
    content_html: Optional[str] = Field(default=None, sa_column=Column(Text))
    content_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # 结构化存储
    
    # 统计
    word_count: Optional[int] = Field(default=None)
    page_count: Optional[int] = Field(default=None)
    screenshot_count: int = Field(default=0)
    
    # 合规检查
    has_toc: bool = Field(default=False)  # 是否有目录
    has_chapters: bool = Field(default=False)  # 是否有规范章节
    
    # 关系
    copyright_data: CopyrightData = Relationship(back_populates="manuals")
    screenshots: List["ManualScreenshot"] = Relationship(back_populates="manual")


class ManualScreenshot(BaseUUIDModel, TimestampMixin, table=True):
    """说明书截图"""
    __tablename__ = "manual_screenshot"
    
    manual_id: UUID = Field(foreign_key="copyright_manual.id")
    upload_id: UUID = Field(foreign_key="file_upload.id")
    
    caption: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    display_order: int = Field(default=0)
    
    # 关系
    manual: CopyrightManual = Relationship(back_populates="screenshots")
```

### 3.6 合规检查模型

```python
# models/compliance.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, String, ForeignKey, DateTime
from sqlalchemy import JSON

from .base import BaseUUIDModel, TimestampMixin


class ComplianceCheck(BaseUUIDModel, TimestampMixin, table=True):
    """合规检查运行记录"""
    __tablename__ = "compliance_check"
    
    project_id: UUID = Field(foreign_key="project.id")
    triggered_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    # 检查类型
    check_type: str = Field(default="full", sa_column=Column(String(20)))  # full, quick, custom
    
    # 结果汇总
    total_rules: int = Field()
    passed_count: int = Field()
    warning_count: int = Field()
    failed_count: int = Field()
    
    overall_status: str = Field(sa_column=Column(String(20)))  # passed, warning, failed
    is_blocking: bool = Field(default=False)  # 是否阻止导出
    
    # 关系
    project: "Project" = Relationship(back_populates="compliance_checks")
    rule_results: List["ComplianceRuleResult"] = Relationship(back_populates="compliance_check")


class ComplianceRuleResult(BaseUUIDModel, table=True):
    """单项合规规则检查结果"""
    __tablename__ = "compliance_rule_result"
    
    compliance_check_id: UUID = Field(foreign_key="compliance_check.id")
    
    # 规则信息
    rule_id: str = Field(sa_column=Column(String(50)))
    rule_name: str = Field(sa_column=Column(String(100)))
    category: str = Field(sa_column=Column(String(50)))  # info, code, manual, proof, claims, etc.
    severity: str = Field(sa_column=Column(String(20)))  # error, warning, info
    
    # 结果
    status: str = Field(sa_column=Column(String(20)))  # passed, failed, warning, skipped
    message: str = Field(sa_column=Column(String(500)))
    suggestion: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # 自动修复信息
    auto_fixable: bool = Field(default=False)
    auto_fix_applied: bool = Field(default=False)
    
    # 关系
    compliance_check: ComplianceCheck = Relationship(back_populates="rule_results")
```

---

## 四、API 设计规范

### 4.1 统一响应格式

```python
# schemas/responses.py
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T')


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    success: bool = True
    code: str = "SUCCESS"
    message: str = "操作成功"
    data: Optional[T] = None
    meta: Optional[dict] = None


class PaginatedResponse(APIResponse, Generic[T]):
    """分页响应格式"""
    data: List[T]
    pagination: PaginationMeta


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    code: str  # 错误代码，如 AUTH_INVALID_TOKEN
    message: str
    details: Optional[dict] = None
    request_id: Optional[str] = None  # 用于日志追踪
```

### 4.2 核心 API 路由

```python
# API 路由结构
/api/v1/
├── /auth
│   ├── POST /login                    # 登录
│   ├── POST /register                 # 注册
│   ├── POST /logout                   # 登出
│   ├── POST /refresh                  # 刷新令牌
│   ├── POST /forgot-password          # 忘记密码
│   ├── POST /reset-password           # 重置密码
│   └── GET  /me                       # 获取当前用户
│
├── /users
│   ├── GET    /                       # 用户列表（管理员）
│   ├── GET    /{id}                   # 用户详情
│   ├── PATCH  /{id}                   # 更新用户
│   ├── DELETE /{id}                   # 删除用户
│   └── PATCH  /{id}/password          # 修改密码
│
├── /organizations
│   ├── GET    /                       # 组织列表
│   ├── POST   /                       # 创建组织
│   ├── GET    /{id}                   # 组织详情
│   ├── PATCH  /{id}                   # 更新组织
│   ├── GET    /{id}/members           # 成员列表
│   ├── POST   /{id}/members           # 添加成员
│   ├── DELETE /{id}/members/{user_id} # 移除成员
│   └── PATCH  /{id}/members/{user_id} # 更新成员角色
│
├── /projects
│   ├── GET    /                       # 项目列表（支持筛选）
│   ├── POST   /                       # 创建项目
│   ├── GET    /{id}                   # 项目详情
│   ├── PATCH  /{id}                   # 更新项目
│   ├── DELETE /{id}                   # 删除项目
│   ├── POST   /{id}/duplicate         # 复制项目
│   ├── GET    /{id}/activities        # 项目活动日志
│   └── GET    /{id}/timeline          # 项目时间线
│
├── /copyright  # 软著模块
│   ├── /projects/{id}
│   │   ├── GET    /software-info      # 获取软件信息
│   │   ├── PUT    /software-info      # 更新软件信息
│   │   ├── GET    /code-bundles       # 代码包列表
│   │   ├── POST   /code-bundles       # 上传代码包
│   │   ├── DELETE /code-bundles/{bid} # 删除代码包
│   │   ├── GET    /manuals            # 说明书列表
│   │   ├── POST   /manuals            # 创建说明书
│   │   ├── PUT    /manuals/{mid}      # 更新说明书
│   │   └── POST   /export             # 导出申请包
│   └── /templates
│       └── GET /manuals               # 说明书模板列表
│
├── /patents    # 专利模块
│   └── /projects/{id}
│       ├── GET/PUT /patent-info       # 专利信息
│       ├── GET/PUT /claims            # 权利要求书
│       ├── GET/PUT /description       # 说明书
│       └── POST    /export            # 导出
│
├── /trademarks # 商标模块
│   └── /projects/{id}
│       ├── GET/PUT /trademark-info    # 商标信息
│       ├── GET/PUT /classifications   # 尼斯分类
│       └── POST    /export            # 导出
│
├── /uploads
│   ├── POST /                         # 上传文件
│   ├── GET  /{id}                     # 获取文件信息
│   ├── GET  /{id}/download            # 下载文件
│   └── DELETE /{id}                   # 删除文件
│
├── /compliance
│   └── /projects/{id}
│       ├── GET  /check                # 获取最新检查结果
│       └── POST /check                # 执行合规检查
│
└── /exports
    ├── GET  /                         # 导出历史
    └── GET  /{id}/download            # 下载导出包
```

---

## 五、关键服务设计

### 5.1 认证服务（JWT + Redis）

```python
# core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis

from config import settings

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis 连接
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# 安全_scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌（短期）"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """创建刷新令牌（长期，存储于 Redis）"""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token_id = secrets.token_urlsafe(32)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": token_id,
        "iat": datetime.utcnow(),
    }
    
    # 存储到 Redis 用于失效
    redis_client.setex(
        f"refresh_token:{token_id}",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        str(user_id)
    )
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def revoke_token(token: str, token_type: str = "access") -> None:
    """撤销令牌（加入黑名单）"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        jti = payload.get("jti")
        
        if exp and jti:
            ttl = exp - int(datetime.utcnow().timestamp())
            if ttl > 0:
                await redis_client.setex(f"blacklist:{token_type}:{jti}", ttl, "1")
    except JWTError:
        pass


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前用户（依赖注入）"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")
        
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查黑名单
        if jti and await redis_client.exists(f"blacklist:access:{jti}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已撤销",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库获取用户
    user = await user_service.get_by_id(UUID(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


# RBAC 权限检查
def require_role(allowed_roles: List[UserRole]):
    """角色权限装饰器"""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return role_checker
```

### 5.2 代码处理服务

```python
# services/copyright/code_processor.py
import zipfile
import io
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

from models.copyright import CodeBundle, CodePageData


# 支持的代码文件扩展名
CODE_EXTENSIONS: Set[str] = {
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.py', '.pyw',
    '.java', '.kt', '.kts', '.scala',
    '.c', '.h', '.cpp', '.hpp', '.cc', '.cxx',
    '.cs', '.vb',
    '.go', '.rs', '.rb', '.php',
    '.swift', '.m', '.mm',
    '.vue', '.svelte',
    '.html', '.htm', '.css', '.scss', '.sass',
    '.sql', '.plsql',
    '.sh', '.bash', '.zsh', '.ps1', '.bat',
    '.xml', '.json', '.yaml', '.yml', '.toml',
    '.lua', '.pl', '.r', '.dart', '.elm',
}

# 忽略目录
IGNORE_DIRS: Set[str] = {
    'node_modules', '.git', '.svn', '.hg', 
    'dist', 'build', 'target', '__pycache__',
    '.idea', '.vscode', '.vs', 'vendor', 
    'bower_components', '.next', '.nuxt', 
    'out', '.cache', 'coverage',
}

LINES_PER_PAGE = 50
PAGES_FIRST = 30
PAGES_LAST = 30
TOTAL_REQUIRED_LINES = LINES_PER_PAGE * (PAGES_FIRST + PAGES_LAST)


class CodeProcessor:
    """代码处理服务"""
    
    async def process_zip(self, file_content: bytes, copyright_data_id: UUID) -> CodeBundle:
        """处理上传的 ZIP 文件"""
        
        # 1. 解压并扫描
        files = await self._extract_code_files(file_content)
        
        if not files:
            raise ValueError("ZIP 文件中未找到代码文件")
        
        # 2. 合并内容
        combined_lines = self._combine_files(files)
        total_lines = len(combined_lines)
        
        # 3. 检查代码量并填充
        has_enough_code = total_lines >= TOTAL_REQUIRED_LINES
        if not has_enough_code:
            combined_lines = self._pad_lines(combined_lines)
        
        # 4. 分页处理
        pages = self._paginate(combined_lines)
        
        # 5. 统计信息
        language_stats = self._analyze_languages(files)
        
        # 6. 创建记录
        code_bundle = CodeBundle(
            copyright_data_id=copyright_data_id,
            original_file_name="source_code.zip",
            original_file_size=len(file_content),
            total_files=len(files),
            total_lines=total_lines,
            processed_lines=len(combined_lines),
            pages_data=[page.dict() for page in pages],
            language_stats=language_stats,
            has_enough_code=has_enough_code,
            warnings=[] if has_enough_code else [f"代码行数不足：需要 {TOTAL_REQUIRED_LINES} 行，实际 {total_lines} 行"]
        )
        
        return code_bundle
    
    async def _extract_code_files(self, content: bytes) -> List[Dict]:
        """从 ZIP 中提取代码文件"""
        files = []
        
        with zipfile.ZipFile(io.BytesIO(content), 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                
                file_path = info.filename
                
                # 检查忽略目录
                if any(part in IGNORE_DIRS for part in file_path.split('/')):
                    continue
                
                # 检查扩展名
                ext = Path(file_path).suffix.lower()
                if ext not in CODE_EXTENSIONS:
                    continue
                
                try:
                    content = zf.read(info).decode('utf-8')
                    lines = content.split('\n')
                    
                    files.append({
                        'path': file_path,
                        'content': content,
                        'lines': lines,
                        'line_count': len(lines),
                        'extension': ext,
                    })
                except (UnicodeDecodeError, Exception):
                    continue
        
        # 按路径排序
        files.sort(key=lambda x: x['path'])
        return files
    
    def _combine_files(self, files: List[Dict]) -> List[str]:
        """合并所有文件内容"""
        combined = []
        
        for file in files:
            combined.append(f"// ============================================================")
            combined.append(f"// File: {file['path']}")
            combined.append(f"// ============================================================")
            combined.extend(file['lines'])
            combined.append('')  # 空行分隔
        
        return combined
    
    def _pad_lines(self, lines: List[str]) -> List[str]:
        """填充代码行以满足页数要求"""
        original = lines.copy()
        
        while len(lines) < TOTAL_REQUIRED_LINES:
            lines.append('')
            lines.append('// ============================================================')
            lines.append('// [Repeated content to meet page requirements]')
            lines.append('// ============================================================')
            lines.extend(original)
            
            if len(lines) > TOTAL_REQUIRED_LINES * 2:  # 防止无限循环
                break
        
        return lines[:TOTAL_REQUIRED_LINES]
    
    def _paginate(self, lines: List[str]) -> List[CodePageData]:
        """分页处理"""
        pages = []
        
        # 前 30 页
        first_section = lines[:LINES_PER_PAGE * PAGES_FIRST]
        for i in range(PAGES_FIRST):
            start_idx = i * LINES_PER_PAGE
            page_lines = first_section[start_idx:start_idx + LINES_PER_PAGE]
            line_start = start_idx + 1
            
            # 添加行号
            numbered_lines = [f"{line_start + j:5d}  {line}" 
                             for j, line in enumerate(page_lines)]
            
            pages.append(CodePageData(
                page_number=i + 1,
                content='\n'.join(numbered_lines),
                line_start=line_start,
                line_end=line_start + len(page_lines) - 1,
                section='first'
            ))
        
        # 后 30 页
        last_section_start = max(len(lines) - LINES_PER_PAGE * PAGES_LAST, 
                                  LINES_PER_PAGE * PAGES_FIRST)
        last_section = lines[last_section_start:]
        
        for i in range(PAGES_LAST):
            start_idx = i * LINES_PER_PAGE
            page_lines = last_section[start_idx:start_idx + LINES_PER_PAGE]
            line_start = last_section_start + start_idx + 1
            
            numbered_lines = [f"{line_start + j:5d}  {line}" 
                             for j, line in enumerate(page_lines)]
            
            pages.append(CodePageData(
                page_number=PAGES_FIRST + i + 1,
                content='\n'.join(numbered_lines),
                line_start=line_start,
                line_end=line_start + len(page_lines) - 1,
                section='last'
            ))
        
        return pages
    
    def _analyze_languages(self, files: List[Dict]) -> Dict[str, int]:
        """分析编程语言分布"""
        stats = defaultdict(int)
        for file in files:
            stats[file['extension']] += file['line_count']
        return dict(stats)
```

---

## 六、前端改进方案

### 6.1 前端架构优化

```
frontend/                          # 前端根目录（原 client/ 重构）
├── package.json
├── vite.config.ts
├── tsconfig.json
│
├── src/
│   ├── main.tsx                   # 应用入口
│   ├── App.tsx                    # 根组件
│   │
│   ├── api/                       # API 客户端（重构）
│   │   ├── client.ts              # axios/fetch 封装
│   │   ├── auth.ts                # 认证相关 API
│   │   ├── projects.ts            # 项目 API
│   │   ├── copyright.ts           # 软著 API
│   │   └── types.ts               # API 类型定义
│   │
│   ├── components/                # 组件
│   │   ├── ui/                    # shadcn/ui 基础组件
│   │   ├── layout/                # 布局组件
│   │   │   ├── app-sidebar.tsx    # 侧边栏（优化版）
│   │   │   ├── header.tsx         # 顶部导航
│   │   │   └── breadcrumbs.tsx    # 面包屑
│   │   ├── common/                # 通用业务组件
│   │   │   ├── data-table/        # 数据表格（支持排序、筛选、分页）
│   │   │   ├── file-uploader/     # 文件上传（支持分片、断点续传）
│   │   │   ├── rich-editor/       # 富文本编辑器
│   │   │   └── code-viewer/       # 代码预览器
│   │   └── project/               # 项目相关组件
│   │       ├── project-card.tsx   # 项目卡片（优化版）
│   │       ├── step-indicator.tsx # 步骤指示器
│   │       └── wizard/            # 向导组件
│   │           ├── step-layout.tsx
│   │           ├── navigation.tsx
│   │           └── progress-tracker.tsx
│   │
│   ├── hooks/                     # 自定义 Hooks
│   │   ├── use-auth.ts            # 认证状态管理（优化）
│   │   ├── use-projects.ts        # 项目数据管理
│   │   ├── use-upload.ts          # 文件上传管理
│   │   └── use-local-storage.ts   # 本地存储
│   │
│   ├── stores/                    # 状态管理（新增 Zustand）
│   │   ├── auth-store.ts          # 认证状态
│   │   ├── ui-store.ts            # UI 状态（主题、侧边栏等）
│   │   └── project-store.ts       # 项目编辑状态
│   │
│   ├── pages/                     # 页面
│   │   ├── auth/                  # 认证页面
│   │   │   ├── login.tsx          # 登录页（优化版）
│   │   │   ├── register.tsx       # 注册页
│   │   │   └── forgot-password.tsx
│   │   ├── dashboard/             # 工作台
│   │   │   └── index.tsx          # 仪表盘（优化版）
│   │   ├── projects/              # 项目管理
│   │   │   ├── list.tsx           # 项目列表（优化版）
│   │   │   ├── new.tsx            # 新建项目
│   │   │   └── detail.tsx         # 项目详情
│   │   ├── copyright/             # 软著模块
│   │   │   ├── wizard/            # 向导页面
│   │   │   │   ├── step1-info.tsx
│   │   │   │   ├── step2-code.tsx
│   │   │   │   ├── step3-manual.tsx
│   │   │   │   └── step4-export.tsx
│   │   │   └── templates/         # 模板选择
│   │   ├── patents/               # 专利模块
│   │   ├── trademarks/            # 商标模块
│   │   ├── settings/              # 设置页面
│   │   └── admin/                 # 管理后台（新增）
│   │
│   ├── lib/                       # 工具库
│   │   ├── utils.ts               # 通用工具
│   │   ├── query-client.ts        # React Query 配置
│   │   ├── constants.ts           # 常量定义
│   │   └── validators.ts          # 表单校验
│   │
│   ├── types/                     # TypeScript 类型
│   │   ├── api.ts                 # API 类型
│   │   ├── models.ts              # 业务模型类型
│   │   └── index.ts
│   │
│   └── styles/                    # 样式
│       ├── globals.css
│       └── theme.css
│
├── public/                        # 静态资源
└── tests/                         # 测试
```

### 6.2 前端关键技术改进

#### 1. 状态管理升级

```typescript
// stores/auth-store.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { api } from '@/api/client';

interface User {
  id: string;
  email: string;
  username: string;
  displayName: string;
  role: 'admin' | 'member' | 'viewer';
  avatarUrl?: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      
      login: async (email, password) => {
        const response = await api.post('/auth/login', { email, password });
        const { user, accessToken, refreshToken } = response.data;
        
        set({ user, accessToken, isAuthenticated: true });
        
        // 存储刷新令牌到 httpOnly cookie（更安全的做法）
        // 或通过其他安全方式管理
      },
      
      logout: async () => {
        await api.post('/auth/logout');
        set({ user: null, accessToken: null, isAuthenticated: false });
      },
      
      refreshToken: async () => {
        try {
          const response = await api.post('/auth/refresh');
          set({ accessToken: response.data.accessToken });
          return true;
        } catch {
          set({ user: null, accessToken: null, isAuthenticated: false });
          return false;
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ user: state.user, accessToken: state.accessToken }),
    }
  )
);
```

#### 2. API 客户端增强

```typescript
// api/client.ts
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from 'sonner';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证令牌
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 统一错误处理、令牌刷新
api.interceptors.response.use(
  (response) => response.data, // 直接返回 data
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    // 401 错误处理 - 尝试刷新令牌
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshed = await useAuthStore.getState().refreshToken();
      if (refreshed) {
        const token = useAuthStore.getState().accessToken;
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${token}`,
        };
        return api(originalRequest);
      }
      
      // 刷新失败，跳转登录
      window.location.href = '/login';
      return Promise.reject(error);
    }
    
    // 统一错误提示
    const message = (error.response?.data as any)?.message || '请求失败';
    toast.error(message);
    
    return Promise.reject(error);
  }
);

export { api };
```

#### 3. 文件上传 Hook（支持分片上传）

```typescript
// hooks/use-upload.ts
import { useState, useCallback } from 'react';
import { api } from '@/api/client';

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

interface UseUploadOptions {
  chunkSize?: number; // 分片大小，默认 5MB
  onProgress?: (progress: UploadProgress) => void;
  onSuccess?: (response: any) => void;
  onError?: (error: Error) => void;
}

export function useUpload(options: UseUploadOptions = {}) {
  const { chunkSize = 5 * 1024 * 1024 } = options;
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);

  const upload = useCallback(async (
    file: File,
    metadata?: Record<string, any>
  ) => {
    setIsUploading(true);
    
    try {
      // 小文件直接上传
      if (file.size <= chunkSize) {
        const formData = new FormData();
        formData.append('file', file);
        if (metadata) {
          formData.append('metadata', JSON.stringify(metadata));
        }
        
        const response = await api.post('/uploads', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            const progress = {
              loaded: e.loaded,
              total: e.total!,
              percentage: Math.round((e.loaded / e.total!) * 100),
            };
            setProgress(progress);
            options.onProgress?.(progress);
          },
        });
        
        options.onSuccess?.(response);
        return response;
      }
      
      // 大文件分片上传（实现省略）
      return await uploadChunked(file, metadata);
      
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    } finally {
      setIsUploading(false);
    }
  }, [chunkSize, options]);

  return { upload, isUploading, progress };
}
```

#### 4. 新增管理后台

```typescript
// pages/admin/layout.tsx
// 管理后台独立布局，包含：
// - 用户管理
// - 组织管理
// - 订阅/计费管理
// - 系统配置
// - 审计日志查看
```

### 6.3 UI/UX 改进点

| 改进项 | 当前状态 | 优化方案 |
|--------|---------|---------|
| **数据表格** | 简单列表 | 使用 `@tanstack/react-table`，支持排序、筛选、分页、行选择 |
| **文件上传** | 基础上传 | 支持拖拽、进度显示、分片上传、断点续传 |
| **代码预览** | 纯文本 | 集成 Monaco Editor 或 Prism.js，语法高亮、行号、搜索 |
| **富文本编辑** | 基础编辑器 | 集成 TipTap 或 Plate.js，支持图片上传、表格、模板插入 |
| **表单体验** | 基础表单 | 使用 `react-hook-form` + `zod`，实时校验、自动保存草稿 |
| **响应式设计** | 桌面优先 | 完善移动端适配，支持平板查看 |
| **深色模式** | 已支持 | 优化配色方案，确保对比度合规 |
| **加载状态** | 简单 loading | 骨架屏、渐进加载、乐观更新 |
| **错误处理** | 简单提示 | 全局错误边界、友好错误页面、重试机制 |

---

## 七、配套管理能力架构

### 7.1 订阅与计费系统

```python
# models/billing.py
from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlmodel import Field, SQLModel, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy import JSON

from .base import BaseUUIDModel, TimestampMixin


class PlanType(str, Enum):
    """订阅计划类型"""
    FREE = "free"
    STARTER = "starter"           # 入门版
    PROFESSIONAL = "professional"  # 专业版
    ENTERPRISE = "enterprise"      # 企业版
    AGENCY = "agency"              # 代理版


class SubscriptionStatus(str, Enum):
    """订阅状态"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class Subscription(BaseUUIDModel, TimestampMixin, table=True):
    """订阅记录"""
    __tablename__ = "subscription"
    
    organization_id: UUID = Field(foreign_key="organization.id", unique=True)
    
    plan_type: PlanType
    status: SubscriptionStatus = Field(default=SubscriptionStatus.TRIALING)
    
    # 时间
    current_period_start: datetime = Field()
    current_period_end: datetime = Field()
    trial_ends_at: Optional[datetime] = Field(default=None)
    canceled_at: Optional[datetime] = Field(default=None)
    
    # 支付信息
    payment_provider: str = Field(default="stripe")  # stripe, alipay, wechat
    payment_provider_subscription_id: Optional[str] = Field(default=None)
    
    # 限额（复制自 Plan，支持单独调整）
    max_projects: int = Field()
    max_storage_bytes: int = Field()
    max_team_members: int = Field()
    features: dict = Field(default={}, sa_column=Column(JSON))


class Plan(BaseUUIDModel, table=True):
    """订阅计划配置"""
    __tablename__ = "plan"
    
    name: str = Field(sa_column=Column(String(50)))
    slug: PlanType = Field(sa_column=Column(String(50), unique=True))
    description: Optional[str] = Field(default=None)
    
    # 定价
    monthly_price_cents: int = Field()  # 美分/分
    yearly_price_cents: int = Field()
    currency: str = Field(default="CNY")
    
    # 限额
    max_projects: int = Field()
    max_storage_bytes: int = Field()
    max_team_members: int = Field()
    
    # 功能开关
    features: dict = Field(sa_column=Column(JSON))  # { "ai_assistant": true, ... }
    
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)


class Invoice(BaseUUIDModel, TimestampMixin, table=True):
    """发票/账单记录"""
    __tablename__ = "invoice"
    
    organization_id: UUID = Field(foreign_key="organization.id")
    subscription_id: UUID = Field(foreign_key="subscription.id")
    
    amount_cents: int = Field()
    currency: str = Field(default="CNY")
    status: str = Field()  # draft, open, paid, void, uncollectible
    
    invoice_number: str = Field(sa_column=Column(String(50), unique=True))
    invoice_pdf_url: Optional[str] = Field(default=None)
    
    period_start: datetime = Field()
    period_end: datetime = Field()
    paid_at: Optional[datetime] = Field(default=None)
```

### 7.2 功能权限矩阵

| 功能 | Free | Starter | Professional | Enterprise | Agency |
|------|------|---------|--------------|------------|--------|
| 项目数量 | 3 | 10 | 50 | 无限 | 500/客户 |
| 存储空间 | 100MB | 1GB | 10GB | 100GB | 1TB |
| 团队成员 | 1 | 3 | 10 | 无限 | 20 |
| 软著申请 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 专利申请 | - | ✓ | ✓ | ✓ | ✓ |
| 商标申请 | - | ✓ | ✓ | ✓ | ✓ |
| PDF 导出 | - | ✓ | ✓ | ✓ | ✓ |
| API 访问 | - | - | ✓ | ✓ | ✓ |
| 白标定制 | - | - | - | ✓ | ✓ |
| 优先支持 | - | - | ✓ | ✓ | ✓ |
| SLA 保障 | - | - | - | ✓ | ✓ |

### 7.3 多租户数据隔离

```python
# api/deps.py - 租户隔离依赖

async def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    x_org_id: Optional[str] = Header(None),  # 从 Header 获取组织 ID
) -> Organization:
    """获取当前组织（多租户上下文）"""
    
    # 超级管理员可指定组织
    if current_user.role == UserRole.SUPER_ADMIN and x_org_id:
        org = await db.get(Organization, UUID(x_org_id))
        if org:
            return org
    
    # 获取用户默认组织
    member = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
        .where(OrganizationMember.organization.is_active == True)
        .order_by(OrganizationMember.joined_at)
    )
    member = member.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=403, detail="用户不属于任何组织")
    
    return member.organization


# 在 API 中使用
@router.get("/projects")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_organization),  # 自动注入租户
    pagination: PaginationParams = Depends(),
):
    """查询自动按 organization_id 过滤"""
    query = select(Project).where(
        Project.organization_id == org.id,
        Project.deleted_at.is_(None)
    )
    # ... 分页处理
```

---

## 八、部署与运维

### 8.1 容器化部署

```dockerfile
# Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制依赖配置
COPY pyproject.toml uv.lock ./

# 安装依赖（使用 uv）
RUN uv pip install --system --no-cache -e .

# 生产镜像
FROM python:3.12-slim

WORKDIR /app

# 复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY src/ ./src/

# 非 root 用户运行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.ipflow.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/ipflow
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
      - minio
    volumes:
      - ./uploads:/app/uploads

  worker:
    build: .
    command: celery -A src.ipflow.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/ipflow
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:18-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=ipflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 8.2 环境配置

```python
# src/ipflow/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # 应用
    APP_NAME: str = "IPFlow"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development, staging, production
    
    # 安全
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 数据库
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: RedisDsn
    
    # 存储
    STORAGE_TYPE: str = "minio"  # minio, s3, local
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_BUCKET: str = "ipflow"
    STORAGE_REGION: str = "us-east-1"
    
    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    # 邮件（用于通知）
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text
    
    # 功能开关
    ENABLE_REGISTRATION: bool = True
    ENABLE_AI_ASSISTANT: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 8.3 监控与日志

```python
# core/logging.py
import json
import logging
import sys
from datetime import datetime
from typing import Any

from config import settings


class JSONFormatter(logging.Formatter):
    """JSON 格式日志（适合 ELK/Loki）"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "organization_id"):
            log_data["organization_id"] = record.organization_id
        
        # 异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 额外数据
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging():
    """配置日志"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    logger.addHandler(handler)
```

### 8.4 CI/CD 配置

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: uv pip install -e ".[dev]"
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret
        run: pytest tests/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -t ipflow:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ipflow:${{ github.sha }}
```

---

## 九、开发规范

### 9.1 Python 代码规范

```toml
# pyproject.toml 中的工具配置
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
    "ASYNC", # flake8-async
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

### 9.2 Git 工作流

```
main ────────────────────────────────────────────►
      │                                              │
      │    feature/copyright-export                   │
      │    ─────────► PR ──► code review ──► merge   │
      │                                              │
      │    bugfix/auth-refresh                        │
      │    ─────────► PR ──► code review ──► merge   │
      │                                              │
      ▼                                              ▼
hotfix ──► 紧急修复 ──► PR ──► merge ──► main ──► tag
```

### 9.3 API 版本策略

- **URL 版本控制**: `/api/v1/`, `/api/v2/`
- **向后兼容**: 新版本至少维护 2 个版本的兼容性
- **弃用通知**: API 响应头中包含 `Deprecation` 和 `Sunset` 信息
- **文档同步**: OpenAPI 文档随代码更新自动发布

---

## 十、风险与对策

| 风险 | 可能性 | 影响 | 对策 |
|------|--------|------|------|
| 数据库迁移复杂 | 中 | 高 | 使用 Alembic 分阶段迁移；保留回滚脚本 |
| 文件存储兼容性 | 低 | 高 | 抽象存储接口；支持多后端切换 |
| 性能瓶颈（大文件） | 中 | 中 | 分片上传；异步处理；CDN 加速 |
| 安全漏洞 | 低 | 高 | 定期依赖扫描；代码审计；Bug Bounty |
| 第三方 API 变更 | 中 | 中 | 封装适配层；监控告警；降级策略 |

---

## 附录

### A. 快速启动命令

```bash
# 1. 克隆项目
git clone <repo-url>
cd ipflow

# 2. 后端启动
cd backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
# 编辑 .env 配置数据库等

alembic upgrade head  # 数据库迁移
uvicorn src.ipflow.main:app --reload  # 启动服务

# 3. 前端启动
cd ../frontend
npm install
npm run dev

# 4. Celery 启动（另一个终端）
cd backend
celery -A src.ipflow.tasks.celery_app worker --loglevel=info
```

### B. 测试策略

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试（需要数据库）
pytest tests/integration/ -v

# 端到端测试
pytest tests/e2e/ -v

# 覆盖率报告
pytest --cov=src --cov-report=html
```

### C. 数据库迁移

```bash
# 生成迁移脚本
alembic revision --autogenerate -m "add copyright models"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1

# 查看历史
alembic history --verbose
```

---

**文档版本**: v2.0-draft  
**最后更新**: 2026-02-17  
**作者**: AI Architect  
