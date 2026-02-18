# IPFlow v2.0 架构设计文档

## 1. 系统概述

### 1.1 架构目标

IPFlow v2.0 采用现代化的微服务-ready架构设计，具备以下特性：

- **高可用**: 无状态服务设计，支持水平扩展
- **高性能**: 异步IO处理，Redis缓存加速
- **可维护**: 清晰的模块边界，完善的文档和测试
- **安全性**: JWT认证，RBAC权限控制，审计日志
- **可扩展**: 插件化设计，易于添加新功能

### 1.2 技术选型

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Web App    │  │   Mobile     │  │   CLI工具    │       │
│  │   (React)    │  │   (PWA)      │  │   (Python)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       网关层 (Nginx)                         │
│         负载均衡 / SSL终止 / 静态文件服务 / 限流              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       应用层 (FastAPI)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  Auth    │ │ Projects │ │Copyright │ │  Admin   │        │
│  │  认证    │ │  项目    │ │  软著    │ │ 管理后台 │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Organizations│ │Subscriptions│ │Compliance │ │ Audit    │ │
│  │ 组织     │ │ 订阅     │ │ 合规     │ │ 审计     │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       服务层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ CodeProcessor│  │ExportGenerator│  │QuotaService │       │
│  │ 代码处理     │  │ 导出生成     │  │ 限额服务    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ComplianceCheck│  │PaymentService│  │AuditLogSvc  │       │
│  │ 合规检查     │  │ 支付服务    │  │ 审计服务    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       数据层                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │PostgreSQL│  │  Redis   │  │  MinIO   │  │  Celery  │    │
│  │ 主数据库 │  │  缓存    │  │ 对象存储 │  │ 任务队列 │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 2. 后端架构

### 2.1 项目结构

```
backend/src/ipflow/
├── api/
│   └── v1/                    # API版本1
│       ├── __init__.py        # 路由聚合
│       ├── auth.py            # 认证API
│       ├── projects.py        # 项目API
│       ├── copyright.py       # 软著API
│       ├── compliance.py      # 合规API
│       ├── organizations.py   # 组织API
│       ├── subscriptions.py   # 订阅API
│       └── admin.py           # 管理后台API
│
├── core/
│   ├── security.py            # 安全工具（JWT、密码）
│   ├── exceptions.py          # 自定义异常
│   ├── logging.py             # 日志配置
│   ├── middleware.py          # 中间件
│   ├── monitoring.py          # 监控指标
│   └── tenant.py              # 多租户上下文
│
├── db/
│   ├── session.py             # 数据库会话
│   └── base.py                # 基础模型
│
├── models/
│   ├── user.py                # 用户模型
│   ├── project.py             # 项目模型
│   ├── copyright.py           # 软著模型
│   ├── organization.py        # 组织模型
│   ├── subscription.py        # 订阅模型
│   ├── audit.py               # 审计日志模型
│   └── enums.py               # 枚举定义
│
├── schemas/
│   ├── auth.py                # 认证Schema
│   ├── subscription.py        # 订阅Schema
│   └── admin.py               # 管理Schema
│
├── services/
│   ├── copyright/
│   │   ├── code_processor.py  # 代码处理
│   │   ├── export_generator.py # 导出生成
│   │   └── compliance_checker.py # 合规检查
│   ├── quota_service.py       # 限额服务
│   ├── payment/
│   │   └── base.py            # 支付基类
│   └── subscriptions/
│       └── service.py         # 订阅服务
│
├── tasks/                     # Celery异步任务
│   └── export_tasks.py
│
├── dependencies.py            # FastAPI依赖
├── config.py                  # 配置管理
└── main.py                    # 应用入口
```

### 2.2 多租户架构

采用**共享数据库，隔离数据**的多租户模式：

```
┌──────────────────────────────────────────────────────────────┐
│                      请求处理流程                            │
│                                                              │
│  Request ──▶ TenantMiddleware ──▶ Extract Tenant ID        │
│                                      │                       │
│                                      ▼                       │
│                              ┌───────────────┐               │
│                              │  ContextVar   │               │
│                              │  tenant_ctx   │               │
│                              └───────────────┘               │
│                                      │                       │
│                                      ▼                       │
│                              ┌───────────────┐               │
│                              │  Database     │               │
│                              │  Query with   │               │
│                              │  WHERE org_id │               │
│                              └───────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

**关键组件:**

1. **TenantContext**: ContextVar管理租户上下文
2. **TenantMiddleware**: 从Header/Query提取租户ID
3. **数据库过滤**: 所有查询自动添加组织过滤

```python
# 租户上下文管理
class TenantContext:
    @staticmethod
    def get_current_tenant_id() -> Optional[str]:
        return tenant_ctx.get()
    
    @staticmethod
    @asynccontextmanager
    async def set_current_tenant_id(tenant_id: str):
        token = tenant_ctx.set(tenant_id)
        try:
            yield
        finally:
            tenant_ctx.reset(token)
```

### 2.3 认证与授权

#### JWT认证流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│  Client │────▶│ /auth/login │────▶│  Verify     │────▶│  JWT    │
│         │     │             │     │  Password   │     │  Token  │
└─────────┘     └─────────────┘     └─────────────┘     └────┬────┘
                                                              │
                                                              ▼
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│ Access  │◀────│   Validate  │◀────│  Decode     │◀────│  Token  │
│ Resource│     │   Token     │     │  JWT        │     │  Header │
└─────────┘     └─────────────┘     └─────────────┘     └─────────┘
```

#### RBAC权限模型

```
超级管理员(super_admin)
    │
    ├── 组织管理员(admin)
    │       ├── 组织经理(manager)
    │       │       ├── 成员(member)
    │       │       └── 查看者(viewer)
    │       └── ...
    └── ...

权限层级:
- super_admin: 系统级管理，访问所有组织
- admin: 组织管理，成员管理，订阅管理
- manager: 项目管理，邀请成员
- member: 创建/编辑项目
- viewer: 只读访问
```

### 2.4 服务层设计

#### 代码处理服务

```python
class CodeProcessor:
    """代码处理服务.
    
    功能:
    - 代码压缩包解析
    - 源代码语言检测
    - 前30页+后30页抽取
    - 行号格式化
    - PDF生成
    """
    
    async def process_upload(
        self,
        file_path: str,
        config: CodeProcessConfig
    ) -> CodeBundle:
        # 1. 解压压缩包
        # 2. 扫描文件树
        # 3. 过滤排除文件
        # 4. 抽取指定页数
        # 5. 格式化输出
        pass
```

#### 限额服务

```python
class QuotaService:
    """限额控制服务.
    
    检查组织的资源使用限制，防止超支。
    """
    
    async def check_project_quota(self, org_id: UUID) -> bool:
        # 检查项目数量是否超限
        
    async def check_storage_quota(
        self, 
        org_id: UUID, 
        additional_bytes: int = 0
    ) -> bool:
        # 检查存储空间是否超限
        
    async def get_usage_stats(self, org_id: UUID) -> dict:
        # 获取资源使用统计
```

## 3. 前端架构

### 3.1 项目结构

```
client/src/
├── components/
│   ├── ui/                    # shadcn/ui 基础组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── layout/                # 布局组件
│   │   ├── sidebar.tsx
│   │   ├── header.tsx
│   │   └── page-container.tsx
│   ├── forms/                 # 表单组件
│   │   ├── project-form.tsx
│   │   └── software-info-form.tsx
│   ├── copyright/             # 软著专用组件
│   │   ├── code-uploader.tsx
│   │   ├── code-viewer.tsx
│   │   └── manual-editor.tsx
│   ├── organization/          # 组织组件
│   │   └── organization-switcher.tsx
│   └── subscription/          # 订阅组件
│       ├── pricing-card.tsx
│       ├── usage-stats.tsx
│       └── invoice-list.tsx
│
├── pages/
│   ├── auth/
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── dashboard.tsx
│   ├── projects/
│   │   ├── index.tsx
│   │   ├── create.tsx
│   │   └── [id]/
│   │       ├── index.tsx
│   │       ├── software-info.tsx
│   │       ├── code-processing.tsx
│   │       ├── manual.tsx
│   │       └── export.tsx
│   ├── organizations/
│   │   ├── index.tsx
│   │   └── settings.tsx
│   ├── subscription.tsx
│   └── admin/
│       ├── dashboard.tsx
│       ├── users.tsx
│       ├── organizations.tsx
│       └── plans.tsx
│
├── stores/
│   ├── auth-store.ts
│   ├── project-store.ts
│   ├── organization-store.ts
│   ├── subscription-store.ts
│   └── admin-store.ts
│
├── types/
│   ├── auth.ts
│   ├── project.ts
│   ├── copyright.ts
│   ├── organization.ts
│   ├── subscription.ts
│   └── admin.ts
│
├── lib/
│   ├── api.ts                 # Axios实例
│   ├── utils.ts               # 工具函数
│   └── constants.ts           # 常量定义
│
└── hooks/
    ├── use-auth.ts
    ├── use-organization.ts
    └── use-subscription.ts
```

### 3.2 状态管理

采用 **Zustand** 进行状态管理，按功能模块拆分：

```typescript
// 认证状态
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

// 组织状态
interface OrganizationState {
  currentOrg: Organization | null;
  organizations: Organization[];
  setCurrentOrg: (org: Organization | null) => void;
  fetchOrganizations: () => Promise<void>;
}

// 订阅状态
interface SubscriptionState {
  currentSubscription: Subscription | null;
  plans: Plan[];
  usageStats: UsageStats | null;
  createSubscription: (planId: string) => Promise<void>;
}
```

### 3.3 路由设计

```typescript
// 路由结构
const routes = [
  // 公开路由
  { path: '/login', component: LoginPage },
  { path: '/register', component: RegisterPage },
  
  // 认证路由
  { 
    path: '/', 
    component: Layout,
    children: [
      { path: '/', component: Dashboard },
      { path: '/projects', component: ProjectList },
      { path: '/projects/create', component: ProjectCreate },
      { path: '/projects/:id', component: ProjectDetail },
      { path: '/projects/:id/software-info', component: SoftwareInfo },
      { path: '/projects/:id/code', component: CodeProcessing },
      { path: '/projects/:id/manual', component: ManualEditor },
      { path: '/projects/:id/export', component: ExportPage },
      { path: '/organizations', component: OrganizationList },
      { path: '/subscription', component: SubscriptionPage },
      
      // 管理员路由
      { path: '/admin', component: AdminDashboard },
      { path: '/admin/users', component: AdminUsers },
      { path: '/admin/organizations', component: AdminOrganizations },
    ]
  }
];
```

## 4. 数据流

### 4.1 项目创建流程

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User   │───▶│ Frontend │───▶│  Backend │───▶│  Database│
└─────────┘    └──────────┘    └──────────┘    └──────────┘
                    │                │                │
                    ▼                ▼                ▼
              1. Fill Form    2. Validate      3. Create Record
              4. Submit       5. Check Quota   6. Return Data
              7. Redirect     8. Return 201
```

### 4.2 代码处理流程

```
User Upload
     │
     ▼
┌─────────────┐
│ 1. Upload   │──▶ Validate (size, type)
│    File     │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 2. Extract  │──▶ Unzip / Clone Git
│    Archive  │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 3. Scan     │──▶ Build file tree
│    Files    │──▶ Detect language
└─────────────┘
     │
     ▼
┌─────────────┐
│ 4. Process  │──▶ Filter ignored files
│    Code     │──▶ Extract 30+30 pages
│             │──▶ Format with line numbers
└─────────────┘
     │
     ▼
┌─────────────┐
│ 5. Generate │──▶ Create PDF
│    PDF      │──▶ Upload to storage
└─────────────┘
     │
     ▼
┌─────────────┐
│ 6. Save     │──▶ Store metadata
│    Result   │
└─────────────┘
```

## 5. 安全设计

### 5.1 认证安全

- **密码安全**: bcrypt 哈希，动态盐值
- **Token安全**: JWT with RS256，短期Access Token + 长期Refresh Token
- **传输安全**: HTTPS only，HSTS头部
- **会话安全**: Redis存储，过期自动清理

### 5.2 数据安全

- **数据库**: 连接加密，敏感字段加密存储
- **文件存储**: 私有Bucket，签名URL访问
- **数据隔离**: 租户ID过滤，防止越权访问
- **备份策略**: 每日自动备份，异地容灾

### 5.3 API安全

- **限流**: 基于IP和用户的双重限流
- **CORS**: 白名单控制
- **输入验证**: Pydantic严格验证
- **SQL注入防护**: ORM参数化查询
- **XSS防护**: 输出编码

## 6. 监控与告警

### 6.1 健康检查

```python
# /health 端点返回
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.5
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.1
    },
    "storage": {
      "status": "healthy"
    }
  }
}
```

### 6.2 监控指标

| 指标 | 类型 | 说明 |
|------|------|------|
| requests_total | Counter | 总请求数 |
| requests_duration | Histogram | 请求处理时间 |
| errors_total | Counter | 错误总数 |
| active_users | Gauge | 当前活跃用户 |
| db_connections | Gauge | 数据库连接数 |

### 6.3 告警规则

- **错误率 > 5%**: 发送告警
- **响应时间 > 2s**: 发送告警
- **磁盘使用 > 80%**: 发送告警
- **数据库连接 > 80%**: 发送告警

## 7. 扩展性设计

### 7.1 水平扩展

```
                    ┌─────────┐
                    │  Nginx  │
                    │ (LB)    │
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ FastAPI │     │ FastAPI │     │ FastAPI │
    │   #1    │     │   #2    │     │   #3    │
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
              ┌─────────────────────┐
              │    PostgreSQL       │
              │  (Primary-Replica)  │
              └─────────────────────┘
```

### 7.2 插件系统

预留插件接口，支持：
- 自定义导出模板
- 第三方存储适配
- 自定义合规规则
- 支付提供商扩展

## 8. 部署架构

### 8.1 Docker Compose (开发/测试)

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ipflow
      - REDIS_URL=redis://redis:6379
  
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  minio:
    image: minio/minio
    command: server /data
```

### 8.2 Kubernetes (生产)

```yaml
# 核心组件
- Deployment: FastAPI App (replicas: 3+)
- Deployment: Celery Worker
- StatefulSet: PostgreSQL
- StatefulSet: Redis
- Deployment: MinIO
- Ingress: Nginx Ingress Controller
- Service: ClusterIP/LoadBalancer
- ConfigMap: 应用配置
- Secret: 敏感信息
```

## 9. 版本演进

| 版本 | 主要特性 | 状态 |
|------|----------|------|
| v1.0 | 基础软著申请功能 | ✅ 已完成 |
| v2.0 | 多租户SaaS、订阅计费 | ✅ 已完成 |
| v2.1 | 专利申请支持 | 🚧 计划中 |
| v2.2 | 商标申请支持 | 📝 待开发 |
| v3.0 | AI辅助撰写 | 📝 待开发 |

## 10. 参考文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [React 文档](https://react.dev/)
- [shadcn/ui 文档](https://ui.shadcn.com/)
