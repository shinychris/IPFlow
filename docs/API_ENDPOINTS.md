# IPFlow API 端点速查

> 完整的 API 文档请参考 [api.md](./api.md) 或启动后端后访问 `/docs`

---

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **协议**: HTTPS (生产环境)
- **认证**: Bearer Token (JWT)
- **请求头**:
  ```
  Authorization: Bearer <access_token>
  X-Tenant-ID: <organization_id>  # 多租户必需
  ```

---

## 端点列表

### 认证模块

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/logout` | 用户登出 |
| POST | `/auth/refresh` | 刷新 Token |
| GET | `/auth/me` | 获取当前用户 |

### 用户管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/users` | 用户列表（管理员） |
| GET | `/users/{id}` | 用户详情 |
| PATCH | `/users/{id}` | 更新用户 |
| DELETE | `/users/{id}` | 删除用户 |
| PATCH | `/users/{id}/password` | 修改密码 |

### 项目管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/projects` | 项目列表（支持筛选） |
| POST | `/projects` | 创建项目 |
| GET | `/projects/{id}` | 项目详情 |
| PATCH | `/projects/{id}` | 更新项目 |
| DELETE | `/projects/{id}` | 删除项目 |
| POST | `/projects/{id}/duplicate` | 复制项目 |
| GET | `/projects/{id}/activities` | 项目活动日志 |
| GET | `/projects/{id}/timeline` | 项目时间线 |

### 软件著作权

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/copyright/projects/{id}/software-info` | 获取软件信息 |
| PUT | `/copyright/projects/{id}/software-info` | 更新软件信息 |
| GET | `/copyright/projects/{id}/code-bundles` | 代码包列表 |
| POST | `/copyright/projects/{id}/code-bundles` | 上传代码包 |
| DELETE | `/copyright/projects/{id}/code-bundles/{bid}` | 删除代码包 |
| GET | `/copyright/projects/{id}/code-bundles/{bid}/preview` | 预览代码 |
| GET | `/copyright/projects/{id}/manuals` | 说明书列表 |
| POST | `/copyright/projects/{id}/manuals` | 创建说明书 |
| PUT | `/copyright/projects/{id}/manuals/{mid}` | 更新说明书 |
| POST | `/copyright/projects/{id}/export` | 导出申请包 |

### 专利模块

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/patents/projects/{id}/patent-info` | 获取专利信息 |
| PUT | `/patents/projects/{id}/patent-info` | 更新专利信息 |
| GET | `/patents/projects/{id}/claims` | 获取权利要求书 |
| PUT | `/patents/projects/{id}/claims` | 更新权利要求书 |
| GET | `/patents/projects/{id}/description` | 获取说明书 |
| PUT | `/patents/projects/{id}/description` | 更新说明书 |
| GET | `/patents/projects/{id}/drawings` | 附图列表 |
| POST | `/patents/projects/{id}/drawings` | 上传附图 |
| DELETE | `/patents/projects/{id}/drawings/{did}` | 删除附图 |
| POST | `/patents/projects/{id}/export` | 导出申请包 |

### 商标模块

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/trademarks/projects/{id}/trademark-info` | 获取商标信息 |
| PUT | `/trademarks/projects/{id}/trademark-info` | 更新商标信息 |
| POST | `/trademarks/projects/{id}/image` | 上传商标图样 |
| GET | `/trademarks/projects/{id}/nice-classes` | 尼斯分类列表 |
| POST | `/trademarks/projects/{id}/nice-classes` | 添加尼斯分类 |
| PUT | `/trademarks/projects/{id}/nice-classes/{cid}` | 更新尼斯分类 |
| DELETE | `/trademarks/projects/{id}/nice-classes/{cid}` | 删除尼斯分类 |
| GET | `/trademarks/nice-classes` | 所有尼斯分类 |
| POST | `/trademarks/projects/{id}/export` | 导出申请包 |

### 文件上传

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/uploads` | 上传文件 |
| GET | `/uploads/{id}` | 获取文件信息 |
| GET | `/uploads/{id}/download` | 下载文件 |
| DELETE | `/uploads/{id}` | 删除文件 |

### 合规检查

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/compliance/projects/{id}` | 获取合规检查 |
| POST | `/compliance/projects/{id}/run` | 执行合规检查 |

### 组织管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/organizations` | 组织列表 |
| POST | `/organizations` | 创建组织 |
| GET | `/organizations/{id}` | 组织详情 |
| PATCH | `/organizations/{id}` | 更新组织 |
| GET | `/organizations/{id}/members` | 成员列表 |
| POST | `/organizations/{id}/members` | 添加成员 |
| DELETE | `/organizations/{id}/members/{user_id}` | 移除成员 |
| PATCH | `/organizations/{id}/members/{user_id}` | 更新成员角色 |
| POST | `/organizations/{id}/invite` | 生成邀请链接 |
| POST | `/organizations/join` | 加入组织 |

### 订阅管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/subscriptions/plans` | 计划列表 |
| GET | `/subscriptions/plans/{id}` | 计划详情 |
| GET | `/subscriptions/current` | 当前订阅 |
| POST | `/subscriptions` | 创建订阅 |
| PATCH | `/subscriptions/{id}` | 更新订阅 |
| DELETE | `/subscriptions/{id}` | 取消订阅 |
| GET | `/subscriptions/invoices` | 发票列表 |
| GET | `/subscriptions/usage` | 使用统计 |
| POST | `/subscriptions/webhook` | 支付 Webhook |

### 管理后台

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/admin/dashboard` | 仪表盘统计 |
| GET | `/admin/users` | 用户列表（管理） |
| GET | `/admin/users/{id}` | 用户详情（管理） |
| PATCH | `/admin/users/{id}` | 更新用户（管理） |
| DELETE | `/admin/users/{id}` | 删除用户（管理） |
| GET | `/admin/organizations` | 组织列表（管理） |
| GET | `/admin/organizations/{id}` | 组织详情（管理） |
| PATCH | `/admin/organizations/{id}` | 更新组织（管理） |
| GET | `/admin/plans` | 计划列表（管理） |
| POST | `/admin/plans` | 创建计划（管理） |
| PATCH | `/admin/plans/{id}` | 更新计划（管理） |
| DELETE | `/admin/plans/{id}` | 删除计划（管理） |
| GET | `/admin/audit-logs` | 审计日志查询 |

---

## 健康检查

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 详细健康检查 |
| GET | `/health/simple` | 简单健康检查 |

---

## 统计

**总计**: 100+ 个 API 端点

| 模块 | 端点数 |
|------|--------|
| 认证 | 5 |
| 用户 | 5 |
| 项目 | 8 |
| 软著 | 10 |
| 专利 | 10 |
| 商标 | 9 |
| 上传 | 4 |
| 合规 | 2 |
| 组织 | 10 |
| 订阅 | 9 |
| 管理 | 14 |
| 其他 | 2 |

---

## 响应状态码

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

---

**最后更新**: 2026-02-28
