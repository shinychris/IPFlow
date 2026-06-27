# IPFlow 数据库文档

## 1. 数据库概述

### 1.1 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 数据库 | PostgreSQL | 14+ |
| ORM | SQLModel | 0.0.x |
| 迁移工具 | Alembic | 1.x |

### 1.2 设计原则

- **类型安全**: 使用 SQLModel 实现 Python 类型和数据库类型的映射
- **软删除**: 重要数据使用 `deleted_at` 字段实现软删除
- **审计字段**: 所有表包含 `created_at` 和 `updated_at`
- **UUID主键**: 使用 UUID v4 作为主键，避免自增ID暴露数据量
- **索引优化**: 常用查询字段添加索引
- **外键约束**: 维护数据完整性

## 2. 实体关系图 (ERD)

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id (PK)         │
│ username (UQ)   │
│ email (UQ)      │
│ password_hash   │
│ role            │
│ status          │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Organization   │◀────│  Organization   │
├─────────────────┤ 1:N ├─────────────────┤
│ id (PK)         │     │ organization_id │
│ name            │     │ user_id (FK)    │
│ slug (UQ)       │     │ role            │
│ plan_type       │     │ joined_at       │
│ max_projects    │     └─────────────────┘
│ max_storage     │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│     Project     │
├─────────────────┤
│ id (PK)         │
│ organization_id │
│ name            │
│ type            │
│ status          │
│ created_by (FK) │
│ created_at      │
└────────┬────────┘
         │
         │ 1:1
         ▼
┌─────────────────┐     ┌─────────────────┐
│ CopyrightData   │◀────│   CodeBundle    │
├─────────────────┤ 1:N ├─────────────────┤
│ id (PK)         │     │ id (PK)         │
│ project_id (FK) │     │ project_id (FK) │
│ software_name   │     │ file_name       │
│ version         │     │ file_size       │
│ rights_holder   │     │ language        │
│ completion_date │     │ total_lines     │
│ city            │     │ status          │
└─────────────────┘     └─────────────────┘
         │
         │ 1:1
         ▼
┌─────────────────┐
│CopyrightManual  │
├─────────────────┤
│ id (PK)         │
│ project_id (FK) │
│ template_type   │
│ content         │
│ page_count      │
│ word_count      │
└─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│      Plan       │◀────│  Subscription   │
├─────────────────┤ 1:N ├─────────────────┤
│ id (PK)         │     │ id (PK)         │
│ name            │     │ organization_id │
│ slug (UQ)       │     │ plan_id (FK)    │
│ price_monthly   │     │ status          │
│ price_yearly    │     │ period_start    │
│ features (JSON) │     │ period_end      │
│ limits (JSON)   │     │ cancel_at_end   │
└─────────────────┘     └─────────────────┘
         ▲
         │
         │ 1:N
┌─────────────────┐
│    Invoice      │
├─────────────────┤
│ id (PK)         │
│ organization_id │
│ subscription_id │
│ amount_due      │
│ amount_paid     │
│ status          │
│ paid_at         │
└─────────────────┘

┌─────────────────┐
│   AuditLog      │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ organization_id │
│ action          │
│ resource_type   │
│ resource_id     │
│ old_values      │
│ new_values      │
│ ip_address      │
│ created_at      │
└─────────────────┘
```

## 3. 表结构详细说明

### 3.1 用户相关

#### users (用户表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| username | VARCHAR(50) | UQ, NOT NULL | 用户名 |
| email | VARCHAR(255) | UQ, NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| display_name | VARCHAR(100) | NULL | 显示名称 |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'user' | 角色 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | 状态 |
| email_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | 邮箱验证 |
| last_login_at | TIMESTAMP | NULL | 最后登录时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引:**
- `idx_users_username` (username)
- `idx_users_email` (email)
- `idx_users_status` (status)

**枚举值:**
- `role`: super_admin, admin, manager, member, viewer
- `status`: active, inactive, suspended

### 3.2 组织相关

#### organizations (组织表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(100) | NOT NULL | 组织名称 |
| slug | VARCHAR(50) | UQ, NOT NULL | 组织标识 |
| description | TEXT | NULL | 描述 |
| business_type | VARCHAR(20) | NULL | 业务类型 |
| license_number | VARCHAR(50) | NULL | 营业执照号 |
| contact_email | VARCHAR(255) | NULL | 联系邮箱 |
| contact_phone | VARCHAR(20) | NULL | 联系电话 |
| plan_type | VARCHAR(20) | NOT NULL, DEFAULT 'free' | 订阅类型 |
| plan_expires_at | TIMESTAMP | NULL | 订阅过期时间 |
| max_projects | INTEGER | NOT NULL, DEFAULT 10 | 最大项目数 |
| max_storage_bytes | BIGINT | NOT NULL, DEFAULT 1073741824 | 最大存储 |
| max_members | INTEGER | NOT NULL, DEFAULT 5 | 最大成员数 |
| used_storage_bytes | BIGINT | NOT NULL, DEFAULT 0 | 已用存储 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否激活 |
| is_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否验证 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| deleted_at | TIMESTAMP | NULL | 删除时间(软删除) |

**索引:**
- `idx_orgs_slug` (slug)
- `idx_orgs_plan_type` (plan_type)
- `idx_orgs_deleted_at` (deleted_at)

#### organization_members (组织成员表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| organization_id | UUID | FK → organizations.id | 组织ID |
| user_id | UUID | FK → users.id | 用户ID |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'member' | 角色 |
| joined_at | TIMESTAMP | NOT NULL | 加入时间 |

**索引:**
- `idx_org_members_org_id` (organization_id)
- `idx_org_members_user_id` (user_id)
- `idx_org_members_unique` (organization_id, user_id) UNIQUE

#### organization_invitations (组织邀请表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| organization_id | UUID | FK → organizations.id | 组织ID |
| inviter_id | UUID | FK → users.id | 邀请人ID |
| email | VARCHAR(255) | NOT NULL | 被邀请邮箱 |
| role | VARCHAR(20) | NOT NULL | 邀请角色 |
| token | VARCHAR(100) | UQ, NOT NULL | 邀请令牌 |
| expires_at | TIMESTAMP | NOT NULL | 过期时间 |
| accepted_at | TIMESTAMP | NULL | 接受时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引:**
- `idx_org_invites_token` (token)
- `idx_org_invites_email` (email)

### 3.3 项目相关

#### projects (项目表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| organization_id | UUID | FK → organizations.id | 组织ID |
| name | VARCHAR(200) | NOT NULL | 项目名称 |
| type | VARCHAR(50) | NOT NULL | 项目类型 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | 状态 |
| description | TEXT | NULL | 描述 |
| subject_type | VARCHAR(20) | NOT NULL | 主体类型 |
| development_method | VARCHAR(30) | NOT NULL | 开发方式 |
| publication_status | VARCHAR(20) | NOT NULL | 发表状态 |
| created_by | UUID | FK → users.id | 创建人 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| deleted_at | TIMESTAMP | NULL | 删除时间 |

**索引:**
- `idx_projects_org_id` (organization_id)
- `idx_projects_status` (status)
- `idx_projects_type` (type)
- `idx_projects_org_status` (organization_id, status)

**枚举值:**
- `type`: software_copyright, patent, trademark
- `status`: draft, active, completed, archived
- `subject_type`: individual, enterprise, institution
- `development_method`: independent, collaborative, commissioned, assignment
- `publication_status`: published, unpublished

### 3.4 软著相关

#### copyright_data (软著数据表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 项目ID |
| software_name | VARCHAR(200) | NOT NULL | 软件全称 |
| software_version | VARCHAR(50) | NULL | 版本号 |
| completion_date | DATE | NULL | 完成日期 |
| rights_holder | VARCHAR(200) | NOT NULL | 著作权人 |
| rights_holder_type | VARCHAR(20) | NOT NULL | 著作权人类型 |
| registration_number | VARCHAR(50) | NULL | 登记号 |
| first_publication_date | DATE | NULL | 首次发表日期 |
| city | VARCHAR(50) | NULL | 城市 |
| description | TEXT | NULL | 软件描述 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引:**
- `idx_copyright_project_id` (project_id) UNIQUE

#### code_bundles (代码包表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 项目ID |
| file_name | VARCHAR(255) | NOT NULL | 文件名 |
| file_size | BIGINT | NOT NULL | 文件大小 |
| file_path | VARCHAR(500) | NOT NULL | 存储路径 |
| mime_type | VARCHAR(100) | NULL | MIME类型 |
| language | VARCHAR(50) | NULL | 编程语言 |
| total_lines | INTEGER | NULL | 总行数 |
| extracted_lines | INTEGER | NULL | 抽取行数 |
| first_n_pages | INTEGER | NOT NULL, DEFAULT 30 | 前N页 |
| last_n_pages | INTEGER | NOT NULL, DEFAULT 30 | 后N页 |
| lines_per_page | INTEGER | NOT NULL, DEFAULT 50 | 每页行数 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | 状态 |
| error_message | TEXT | NULL | 错误信息 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引:**
- `idx_code_bundle_project_id` (project_id)
- `idx_code_bundle_status` (status)

**枚举值:**
- `status`: pending, processing, completed, failed

#### copyright_manuals (操作手册表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 项目ID |
| template_type | VARCHAR(30) | NOT NULL | 模板类型 |
| title | VARCHAR(200) | NOT NULL | 标题 |
| content | TEXT | NOT NULL | 内容 |
| page_count | INTEGER | NULL | 页数 |
| word_count | INTEGER | NULL | 字数 |
| screenshot_count | INTEGER | NULL, DEFAULT 0 | 截图数量 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引:**
- `idx_manual_project_id` (project_id) UNIQUE

**枚举值:**
- `template_type`: web_application, mobile_app, algorithm, script_tool, desktop_software

### 3.5 订阅相关

#### plans (订阅计划表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(100) | NOT NULL | 计划名称 |
| slug | VARCHAR(50) | UQ, NOT NULL | 计划标识 |
| description | TEXT | NULL | 描述 |
| price_monthly | DECIMAL(10,2) | NOT NULL | 月付价格 |
| price_yearly | DECIMAL(10,2) | NOT NULL | 年付价格 |
| currency | VARCHAR(3) | NOT NULL, DEFAULT 'CNY' | 货币 |
| features | JSON | NOT NULL, DEFAULT '[]' | 功能列表 |
| limits | JSON | NOT NULL, DEFAULT '{}' | 资源限制 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否可用 |
| is_public | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否公开 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引:**
- `idx_plans_slug` (slug)
- `idx_plans_is_active` (is_active)

#### subscriptions (订阅表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| organization_id | UUID | FK → organizations.id | 组织ID |
| plan_id | UUID | FK → plans.id | 计划ID |
| status | VARCHAR(20) | NOT NULL | 状态 |
| current_period_start | TIMESTAMP | NOT NULL | 当前周期开始 |
| current_period_end | TIMESTAMP | NOT NULL | 当前周期结束 |
| cancel_at_period_end | BOOLEAN | NOT NULL, DEFAULT FALSE | 到期取消 |
| canceled_at | TIMESTAMP | NULL | 取消时间 |
| trial_start | TIMESTAMP | NULL | 试用开始 |
| trial_end | TIMESTAMP | NULL | 试用结束 |
| payment_provider | VARCHAR(50) | NULL | 支付提供商 |
| payment_provider_subscription_id | VARCHAR(255) | NULL | 外部订阅ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引:**
- `idx_subscriptions_org_id` (organization_id)
- `idx_subscriptions_status` (status)
- `idx_subscriptions_period_end` (current_period_end)

**枚举值:**
- `status`: active, canceled, past_due, unpaid, trialing

#### invoices (发票表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| organization_id | UUID | FK → organizations.id | 组织ID |
| subscription_id | UUID | FK → subscriptions.id | 订阅ID |
| status | VARCHAR(20) | NOT NULL | 状态 |
| amount_due | DECIMAL(10,2) | NOT NULL | 应付金额 |
| amount_paid | DECIMAL(10,2) | NOT NULL, DEFAULT 0 | 已付金额 |
| currency | VARCHAR(3) | NOT NULL, DEFAULT 'CNY' | 货币 |
| description | TEXT | NULL | 描述 |
| lines | JSON | NOT NULL, DEFAULT '[]' | 明细行 |
| payment_provider | VARCHAR(50) | NULL | 支付提供商 |
| payment_provider_invoice_id | VARCHAR(255) | NULL | 外部发票ID |
| hosted_invoice_url | VARCHAR(500) | NULL | 发票URL |
| pdf_url | VARCHAR(500) | NULL | PDF URL |
| paid_at | TIMESTAMP | NULL | 支付时间 |
| due_date | TIMESTAMP | NULL | 到期日期 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引:**
- `idx_invoices_org_id` (organization_id)
- `idx_invoices_status` (status)
- `idx_invoices_created_at` (created_at)

**枚举值:**
- `status`: draft, open, paid, uncollectible, void

### 3.6 审计相关

#### audit_logs (审计日志表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK → users.id, NULL | 用户ID |
| organization_id | UUID | FK → organizations.id, NULL | 组织ID |
| action | VARCHAR(50) | NOT NULL | 操作类型 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型 |
| resource_id | UUID | NULL | 资源ID |
| old_values | JSON | NULL | 旧值 |
| new_values | JSON | NULL | 新值 |
| description | TEXT | NULL | 描述 |
| ip_address | VARCHAR(45) | NULL | IP地址 |
| user_agent | VARCHAR(500) | NULL | 用户代理 |
| request_id | VARCHAR(100) | NULL | 请求ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引:**
- `idx_audit_org_id` (organization_id)
- `idx_audit_user_id` (user_id)
- `idx_audit_action` (action)
- `idx_audit_resource_type` (resource_type)
- `idx_audit_created_at` (created_at)
- `idx_audit_request_id` (request_id)

**枚举值:**
- `action`: create, update, delete, login, logout, export, invite
- `resource_type`: project, user, organization, code_bundle, manual, subscription

## 4. 数据库操作

### 4.1 常用查询

```sql
-- 查询用户的组织和角色
SELECT o.name, om.role
FROM organizations o
JOIN organization_members om ON o.id = om.organization_id
WHERE om.user_id = 'user-uuid';

-- 查询组织的资源使用情况
SELECT 
    o.name,
    o.max_projects,
    COUNT(p.id) as project_count,
    o.max_storage_bytes,
    o.used_storage_bytes,
    o.max_members,
    COUNT(om.id) as member_count
FROM organizations o
LEFT JOIN projects p ON o.id = p.organization_id AND p.deleted_at IS NULL
LEFT JOIN organization_members om ON o.id = om.organization_id
WHERE o.id = 'org-uuid'
GROUP BY o.id;

-- 查询活跃订阅
SELECT 
    s.id,
    o.name as org_name,
    p.name as plan_name,
    s.status,
    s.current_period_end
FROM subscriptions s
JOIN organizations o ON s.organization_id = o.id
JOIN plans p ON s.plan_id = p.id
WHERE s.status = 'active'
AND s.current_period_end > NOW();

-- 查询审计日志（最近24小时）
SELECT *
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 100;
```

### 4.2 性能优化

```sql
-- 查看慢查询
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 查看表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 查看索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 5. 备份与恢复

### 5.1 备份策略

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/ipflow"
DB_NAME="ipflow"
DB_USER="ipflow"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cd $BACKUP_DIR
pg_dump -h localhost -U $DB_USER -d $DB_NAME > db_$DATE.sql

# 压缩备份
tar -czf db_$DATE.sql.tar.gz db_$DATE.sql
rm db_$DATE.sql

# 保留最近30天
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: db_$DATE.sql.tar.gz"
```

### 5.2 恢复数据

```bash
# 解压备份
tar -xzf db_20240115_120000.sql.tar.gz

# 恢复数据库
psql -h localhost -U ipflow -d ipflow < db_20240115_120000.sql

# 或使用 pg_restore（如果是自定义格式）
pg_restore -h localhost -U ipflow -d ipflow backup.dump
```

## 6. 数据库迁移

### 6.1 创建迁移

```bash
# 自动检测变更
alembic revision --autogenerate -m "add new table"

# 手动创建
alembic revision -m "custom migration"
```

### 6.2 常见迁移操作

```python
# 添加列
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone')

# 创建索引
def upgrade():
    op.create_index('idx_users_phone', 'users', ['phone'])

def downgrade():
    op.drop_index('idx_users_phone', 'users')

# 修改列类型
def upgrade():
    op.alter_column('projects', 'description',
                    existing_type=sa.VARCHAR(500),
                    type_=sa.TEXT())

def downgrade():
    op.alter_column('projects', 'description',
                    existing_type=sa.TEXT(),
                    type_=sa.VARCHAR(500))

# 数据迁移
def upgrade():
    # 添加新列
    op.add_column('users', sa.Column('full_name', sa.String(200)))
    
    # 迁移数据
    op.execute("UPDATE users SET full_name = display_name")
    
    # 删除旧列
    op.drop_column('users', 'display_name')

def downgrade():
    op.add_column('users', sa.Column('display_name', sa.String(100)))
    op.execute("UPDATE users SET display_name = full_name")
    op.drop_column('users', 'full_name')
```

## 7. 监控与维护

### 7.1 定期维护任务

```sql
-- 更新统计信息
ANALYZE;

-- 清理死元组
VACUUM ANALYZE;

-- 重建索引
REINDEX DATABASE ipflow;

-- 查看连接数
SELECT count(*) FROM pg_stat_activity;

-- 查看锁等待
SELECT * FROM pg_locks WHERE NOT granted;
```

### 7.2 连接池配置

```python
# 推荐的连接池配置
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # 连接池大小
    max_overflow=30,           # 最大溢出连接
    pool_pre_ping=True,        # 连接前ping检测
    pool_recycle=3600,         # 连接回收时间
    echo=False,                # SQL日志
)
```

## 8. 扩展设计

### 8.1 分区表设计（大数据量）

```sql
-- 审计日志分区表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    -- ... 其他字段
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE audit_logs_2024_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

### 8.2 读写分离

```python
# 主库（写）
write_engine = create_async_engine(MASTER_DATABASE_URL)

# 从库（读）
read_engine = create_async_engine(REPLICA_DATABASE_URL)

# 根据操作类型选择
async def get_db(read_only: bool = False):
    if read_only:
        async with read_session() as session:
            yield session
    else:
        async with write_session() as session:
            yield session
```
