# IPFlow API 文档

## 1. API概述

### 1.1 基本信息

- **Base URL**: `http://localhost:8000/api/v1`
- **协议**: HTTPS (生产环境)
- **数据格式**: JSON
- **认证方式**: Bearer Token (JWT)

### 1.2 通用响应格式

**成功响应:**
```json
{
  "data": { ... },
  "message": "Success"
}
```

**分页响应:**
```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**错误响应:**
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

### 1.3 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 无内容（删除成功） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 验证错误 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 1.4 认证方式

所有API（除认证相关）需要在请求头中携带Token：

```http
Authorization: Bearer <access_token>
X-Tenant-ID: <organization_id>  # 多租户必需
```

## 2. 认证模块

### 2.1 用户注册

```http
POST /auth/register
```

**请求体:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "display_name": "John Doe"
}
```

**响应:**
```json
{
  "id": "uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "display_name": "John Doe",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 2.2 用户登录

```http
POST /auth/login
```

**请求体:**
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user"
  }
}
```

### 2.3 刷新Token

```http
POST /auth/refresh
```

**请求体:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2.4 获取当前用户

```http
GET /auth/me
```

**响应:**
```json
{
  "id": "uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "display_name": "John Doe",
  "role": "user",
  "status": "active",
  "email_verified": true,
  "created_at": "2024-01-15T10:00:00Z",
  "last_login_at": "2024-01-15T10:30:00Z"
}
```

### 2.5 登出

```http
POST /auth/logout
```

**响应:**
```json
{
  "message": "Successfully logged out"
}
```

## 3. 项目模块

### 3.1 获取项目列表

```http
GET /projects?page=1&per_page=20&status=active
```

**查询参数:**
- `page`: 页码 (默认: 1)
- `per_page`: 每页数量 (默认: 20, 最大: 100)
- `status`: 项目状态过滤
- `type`: 项目类型过滤

**响应:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "软件著作权项目",
      "type": "software_copyright",
      "status": "active",
      "version": "1.0.0",
      "progress": 75,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50
  }
}
```

### 3.2 创建项目

```http
POST /projects
```

**请求体:**
```json
{
  "name": "软件著作权项目",
  "type": "software_copyright",
  "description": "项目描述",
  "subject_type": "enterprise",
  "development_method": "independent",
  "publication_status": "unpublished"
}
```

**响应:**
```json
{
  "id": "uuid",
  "name": "软件著作权项目",
  "type": "software_copyright",
  "status": "draft",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 3.3 获取项目详情

```http
GET /projects/{project_id}
```

**响应:**
```json
{
  "id": "uuid",
  "name": "软件著作权项目",
  "type": "software_copyright",
  "status": "active",
  "description": "项目描述",
  "subject_type": "enterprise",
  "development_method": "independent",
  "publication_status": "unpublished",
  "version": "1.0.0",
  "progress": 75,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "created_by": {
    "id": "uuid",
    "username": "john_doe",
    "display_name": "John Doe"
  }
}
```

### 3.4 更新项目

```http
PUT /projects/{project_id}
```

**请求体:**
```json
{
  "name": "新项目名称",
  "description": "新描述",
  "status": "active"
}
```

### 3.5 删除项目

```http
DELETE /projects/{project_id}
```

## 4. 软著模块

### 4.1 获取软件信息

```http
GET /copyright/{project_id}/software-info
```

**响应:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "software_name": "软件全称",
  "software_version": "V1.0",
  "completion_date": "2024-01-15",
  "rights_holder": "公司名称",
  "rights_holder_type": "enterprise",
  "registration_number": "",
  "first_publication_date": null,
  "city": "北京",
  "description": "软件功能描述"
}
```

### 4.2 更新软件信息

```http
PUT /copyright/{project_id}/software-info
```

**请求体:**
```json
{
  "software_name": "软件全称",
  "software_version": "V1.0",
  "completion_date": "2024-01-15",
  "rights_holder": "公司名称",
  "description": "软件功能描述"
}
```

### 4.3 上传代码压缩包

```http
POST /copyright/{project_id}/code-bundle
Content-Type: multipart/form-data
```

**请求体:**
```
code_file: <binary>
extract_config: {
  "first_n_pages": 30,
  "last_n_pages": 30,
  "lines_per_page": 50
}
```

**响应:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "file_name": "source_code.zip",
  "file_size": 1048576,
  "file_path": "projects/uuid/code/source_code.zip",
  "language": "Python",
  "total_lines": 5000,
  "extracted_lines": 3000,
  "status": "processed",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 4.4 获取代码包列表

```http
GET /copyright/{project_id}/code-bundles
```

### 4.5 获取代码预览

```http
GET /copyright/{project_id}/code-bundle/{bundle_id}/preview?page=1
```

**响应:**
```json
{
  "page": 1,
  "total_pages": 60,
  "content": "代码内容...",
  "page_header": "软件全称 V1.0"
}
```

### 4.6 创建操作手册

```http
POST /copyright/{project_id}/manual
```

**请求体:**
```json
{
  "template_type": "web_application",
  "title": "操作手册标题",
  "content": "手册内容...",
  "screenshots": [
    {
      "file_id": "uuid",
      "caption": "图1 系统首页"
    }
  ]
}
```

### 4.7 获取操作手册

```http
GET /copyright/{project_id}/manual
```

## 5. 合规检查模块

### 5.1 执行合规检查

```http
POST /compliance/{project_id}/check
```

**响应:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "status": "completed",
  "results": [
    {
      "rule_code": "SC-001",
      "rule_name": "软件名称检查",
      "status": "passed",
      "message": "软件名称符合规范"
    },
    {
      "rule_code": "SC-002",
      "rule_name": "代码页数检查",
      "status": "failed",
      "message": "代码页数不足60页"
    }
  ],
  "score": 85,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 5.2 获取合规检查结果

```http
GET /compliance/{project_id}/results
```

## 6. 组织模块

### 6.1 获取组织列表

```http
GET /organizations
```

**响应:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "我的公司",
      "slug": "my-company",
      "plan_type": "pro",
      "member_count": 5,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 6.2 创建组织

```http
POST /organizations
```

**请求体:**
```json
{
  "name": "我的公司",
  "slug": "my-company",
  "description": "公司描述"
}
```

### 6.3 获取组织详情

```http
GET /organizations/{org_id}
```

### 6.4 更新组织

```http
PUT /organizations/{org_id}
```

### 6.5 获取组织成员

```http
GET /organizations/{org_id}/members
```

**响应:**
```json
{
  "data": [
    {
      "id": "uuid",
      "user": {
        "id": "uuid",
        "username": "john_doe",
        "display_name": "John Doe",
        "avatar": "https://..."
      },
      "role": "admin",
      "joined_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 6.6 邀请成员

```http
POST /organizations/{org_id}/invite
```

**请求体:**
```json
{
  "email": "new_member@example.com",
  "role": "member"
}
```

### 6.7 接受邀请

```http
POST /organizations/invite/accept
```

**请求体:**
```json
{
  "token": "invite_token"
}
```

## 7. 订阅模块

### 7.1 获取计划列表

```http
GET /subscriptions/plans
```

**响应:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "免费版",
      "slug": "free",
      "description": "适合个人开发者",
      "price_monthly": 0,
      "price_yearly": 0,
      "currency": "CNY",
      "features": ["最多3个项目", "100MB存储", "基础支持"],
      "limits": {
        "max_projects": 3,
        "max_storage_gb": 0.1,
        "max_members": 1
      }
    },
    {
      "id": "uuid",
      "name": "专业版",
      "slug": "pro",
      "description": "适合小型团队",
      "price_monthly": 99,
      "price_yearly": 999,
      "currency": "CNY",
      "features": ["无限项目", "10GB存储", "团队协作", "优先支持"],
      "limits": {
        "max_projects": -1,
        "max_storage_gb": 10,
        "max_members": 10
      }
    }
  ]
}
```

### 7.2 获取当前订阅

```http
GET /subscriptions/current
```

**响应:**
```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "plan": {
    "id": "uuid",
    "name": "专业版",
    "slug": "pro"
  },
  "status": "active",
  "current_period_start": "2024-01-01T00:00:00Z",
  "current_period_end": "2024-02-01T00:00:00Z",
  "cancel_at_period_end": false
}
```

### 7.3 创建订阅

```http
POST /subscriptions
```

**请求体:**
```json
{
  "plan_id": "uuid",
  "interval": "monthly"
}
```

### 7.4 更新订阅

```http
PATCH /subscriptions
```

**请求体:**
```json
{
  "plan_id": "uuid",
  "cancel_at_period_end": false
}
```

### 7.5 取消订阅

```http
POST /subscriptions/cancel?at_period_end=true
```

### 7.6 获取发票列表

```http
GET /subscriptions/invoices
```

**响应:**
```json
{
  "data": [
    {
      "id": "uuid",
      "amount_due": 99.00,
      "amount_paid": 99.00,
      "currency": "CNY",
      "status": "paid",
      "description": "专业版月付",
      "hosted_invoice_url": "https://...",
      "pdf_url": "https://...",
      "paid_at": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 7.7 获取使用统计

```http
GET /subscriptions/usage
```

**响应:**
```json
{
  "projects": {
    "used": 5,
    "limit": 10,
    "remaining": 5,
    "percentage": 50
  },
  "storage": {
    "used_bytes": 536870912,
    "limit_bytes": 10737418240,
    "remaining_bytes": 10200547328,
    "percentage": 5,
    "used_gb": 0.5,
    "limit_gb": 10
  },
  "members": {
    "used": 3,
    "limit": 10,
    "remaining": 7,
    "percentage": 30
  }
}
```

## 8. 管理后台模块

### 8.1 获取仪表盘统计

```http
GET /admin/dashboard
```

**响应:**
```json
{
  "total_users": 1000,
  "new_users_this_month": 50,
  "total_organizations": 200,
  "active_subscriptions": 150,
  "revenue_this_month": 15000.00,
  "total_projects": 500
}
```

### 8.2 获取用户列表

```http
GET /admin/users?page=1&per_page=20&search=keyword
```

### 8.3 更新用户

```http
PATCH /admin/users/{user_id}
```

**请求体:**
```json
{
  "role": "admin",
  "status": "active",
  "email_verified": true
}
```

### 8.4 删除用户

```http
DELETE /admin/users/{user_id}
```

### 8.5 获取组织列表

```http
GET /admin/organizations?page=1&per_page=20
```

### 8.6 更新组织

```http
PATCH /admin/organizations/{org_id}
```

**请求体:**
```json
{
  "plan_type": "enterprise",
  "max_projects": 100,
  "is_verified": true
}
```

### 8.7 获取计划列表

```http
GET /admin/plans
```

### 8.8 创建计划

```http
POST /admin/plans
```

**请求体:**
```json
{
  "name": "企业版",
  "slug": "enterprise",
  "description": "适合大型企业",
  "price_monthly": 999,
  "price_yearly": 9999,
  "features": ["无限项目", "无限存储", "SSO", "专属支持"],
  "limits": {
    "max_projects": -1,
    "max_storage_gb": -1,
    "max_members": -1
  }
}
```

### 8.9 获取审计日志

```http
GET /admin/audit-logs?page=1&per_page=50&action=create&resource_type=project
```

**响应:**
```json
{
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "organization_id": "uuid",
      "action": "create",
      "resource_type": "project",
      "resource_id": "uuid",
      "description": "创建项目",
      "ip_address": "192.168.1.1",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

## 9. 文件上传模块

### 9.1 上传文件

```http
POST /uploads/
Content-Type: multipart/form-data
```

**请求体:**
```
file: <binary>
project_id: "uuid"          # 可选，关联项目
purpose: "code_bundle"      # 用途：code_bundle, screenshot, proof
```

**响应:**
```json
{
  "id": "uuid",
  "file_name": "source_code.zip",
  "file_size": 1048576,
  "mime_type": "application/zip",
  "file_path": "uploads/uuid/source_code.zip",
  "url": "https://storage.example.com/...",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 9.2 获取文件信息

```http
GET /uploads/{file_id}
```

### 9.3 删除文件

```http
DELETE /uploads/{file_id}
```

## 10. Webhook

### 10.1 支付提供商Webhook

```http
POST /subscriptions/webhook/{provider}
```

**路径参数:**
- `provider`: `stripe` | `alipay` | `wechat_pay`

**头部:**
```http
Stripe-Signature: signature
```

用于接收支付提供商的异步通知。

## 11. 健康检查

### 11.1 简单健康检查

```http
GET /health/simple
```

**响应:**
```json
{
  "status": "healthy"
}
```

### 11.2 详细健康检查

```http
GET /health
```

**响应:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "timestamp": "2024-01-15T10:00:00Z",
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

## 12. 错误代码

| 错误代码 | 描述 | HTTP状态码 |
|----------|------|------------|
| `INVALID_CREDENTIALS` | 用户名或密码错误 | 401 |
| `USER_INACTIVE` | 用户账号未激活 | 403 |
| `EMAIL_EXISTS` | 邮箱已被注册 | 400 |
| `USERNAME_EXISTS` | 用户名已被使用 | 400 |
| `ORGANIZATION_NOT_FOUND` | 组织不存在 | 404 |
| `INSUFFICIENT_PERMISSIONS` | 权限不足 | 403 |
| `QUOTA_EXCEEDED` | 超出资源限额 | 400 |
| `INVALID_FILE_TYPE` | 不支持的文件类型 | 400 |
| `FILE_TOO_LARGE` | 文件大小超限 | 400 |
| `PAYMENT_FAILED` | 支付失败 | 400 |
