# 贡献指南

感谢您对 IPFlow 项目的关注！我们欢迎各种形式的贡献，包括但不限于：

- 报告问题
- 提交功能建议
- 改进文档
- 提交代码修复
- 添加新功能

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [审查流程](#审查流程)
- [发布流程](#发布流程)

## 行为准则

本项目采用 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。参与本项目即表示您同意遵守此准则。

### 我们的承诺

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请通过 [GitHub Issues](https://github.com/your-org/ipflow/issues) 提交。

**提交 issue 前请确认：**

- [ ] 已经搜索过现有 issues，避免重复
- [ ] 使用的是最新版本
- [ ] 提供了清晰的问题描述
- [ ] 提供了复现步骤（如果是 bug）
- [ ] 提供了期望的行为和实际的行为
- [ ] 提供了环境信息（操作系统、浏览器等）

**Bug 报告模板:**

```markdown
## 问题描述
简要描述遇到的问题

## 复现步骤
1. 进入 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 期望行为
清晰描述期望发生什么

## 实际行为
描述实际发生了什么

## 截图
如有必要，添加截图

## 环境信息
- OS: [例如 macOS, Windows]
- 浏览器: [例如 Chrome, Safari]
- 版本: [例如 22]

## 附加信息
其他相关信息
```

### 提交代码

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

## 开发环境搭建

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Git

### 快速开始

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/YOUR_USERNAME/ipflow.git
cd ipflow

# 2. 添加上游仓库
git remote add upstream https://github.com/your-org/ipflow.git

# 3. 安装后端依赖
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 4. 安装前端依赖
cd ../client
npm install

# 5. 配置环境变量
cp ../backend/.env.example ../backend/.env
cp .env.example .env.local

# 6. 启动开发服务器
# 终端1: 后端
cd ../backend
uvicorn ipflow.main:app --reload

# 终端2: 前端
cd ../client
npm run dev
```

详细开发指南请参考 [docs/development.md](docs/development.md)

## 代码规范

### Python 代码规范

我们使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **ruff**: 代码检查
- **mypy**: 类型检查

```bash
# 格式化代码
black src/ tests/
isort src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/
```

### TypeScript 代码规范

```bash
# 格式化
cd client
npm run format

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

### 代码风格要求

#### Python

- 使用类型注解
- 函数和类添加文档字符串
- 复杂逻辑添加注释
- 遵循 PEP 8 规范

```python
from typing import Optional
from uuid import UUID

async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID
) -> Optional[User]:
    """根据ID获取用户.
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        用户对象，如果不存在则返回 None
        
    Raises:
        DatabaseError: 数据库查询失败
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

#### TypeScript

- 使用严格类型
- 组件添加 JSDoc
- 避免使用 `any`

```typescript
interface UserProps {
  id: string;
  name: string;
  email: string;
}

/**
 * 用户卡片组件
 * @param props - 组件属性
 */
export function UserCard({ id, name, email }: UserProps) {
  return (
    <div className="user-card">
      <h3>{name}</h3>
      <p>{email}</p>
    </div>
  );
}
```

## 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）:**

- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式（不影响代码运行的变动）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建过程或辅助工具的变动

**范围（scope）:**

- `backend`: 后端
- `frontend`: 前端
- `db`: 数据库
- `api`: API
- `auth`: 认证
- `copyright`: 软著功能
- `org`: 组织功能
- `billing`: 计费功能

**示例:**

```
feat(backend): 添加用户注册功能

- 实现用户模型
- 添加注册 API
- 发送验证邮件

Closes #123
```

```
fix(frontend): 修复代码上传进度显示错误

修复大文件上传时进度条不更新的问题

Fixes #456
```

```
docs: 更新 API 文档

添加新的认证接口说明
```

### 提交前检查

```bash
# 运行测试
pytest
npm test

# 检查代码风格
make lint

# 检查类型
make type-check
```

## 审查流程

### Pull Request 规范

**标题格式:**
```
[<type>][<scope>] <description>
```

例如: `[feat][backend] 添加组织邀请功能`

**PR 描述模板:**

```markdown
## 描述
简要描述这个 PR 做了什么

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了测试
- [ ] 所有测试通过
- [ ] 更新了文档
- [ ] 添加了必要的注释

## 相关 Issue
Fixes #(issue 编号)

## 截图（如有 UI 变更）
```

### 审查标准

**必须满足:**
- [ ] 代码符合项目规范
- [ ] 有足够的测试覆盖
- [ ] 所有测试通过
- [ ] 没有安全漏洞
- [ ] 性能影响评估

**建议满足:**
- [ ] 代码简洁易读
- [ ] 有适当的注释
- [ ] 文档已更新

### 合并策略

我们使用 **Squash Merge** 策略，确保主分支历史清晰。

## 发布流程

### 版本号规则

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

- `MAJOR`: 不兼容的 API 修改
- `MINOR`: 向下兼容的功能新增
- `PATCH`: 向下兼容的问题修复

### 发布步骤

1. 更新版本号（`pyproject.toml` 和 `package.json`）
2. 更新 `CHANGELOG.md`
3. 创建发布分支：`git checkout -b release/vX.X.X`
4. 提交变更：`git commit -m "chore: release vX.X.X"`
5. 创建 PR 并合并到 main
6. 打标签：`git tag -a vX.X.X -m "Release vX.X.X"`
7. 推送标签：`git push origin vX.X.X`
8. 在 GitHub 创建 Release

## 开发资源

### 文档

- [架构设计](docs/architecture.md)
- [API 文档](docs/api.md)
- [开发指南](docs/development.md)
- [数据库文档](docs/database.md)
- [部署指南](docs/deployment.md)

### 工具

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Zustand 文档](https://docs.pmnd.rs/zustand)

## 社区

- [GitHub Discussions](https://github.com/your-org/ipflow/discussions)
- [Discord](https://discord.gg/ipflow)
- [Twitter](https://twitter.com/ipflow)

## 许可证

通过贡献代码，您同意您的贡献将在 [MIT 许可证](LICENSE) 下发布。

---

**感谢您对 IPFlow 的贡献！** 🎉
