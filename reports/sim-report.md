# IPFlow 仿真可用性测试报告

**生成时间**: 2026-06-28 01:00:40
  |  **形态**: web
  |  **被测目标**: `http://localhost:3000`
  |  **开始时间**: 2026-06-27T15:37:01Z


## 测试章程
> 新用户从注册到软著/专利/商标三大业务材料生成与导出的完整流程，验证真实可用性与生成结果

## 探索概览

| 操作步数 | 通过 | 警告 | 失败 | 发现问题数 |
|---|---|---|---|---|
| 11 | 11 | 0 | 0 | 9 |

## 发现的问题

| # | 严重程度 | 类型 | 问题 |
|---|---|---|---|
| 2 | 严重 | 功能 | 软著合规检查崩溃 500（None>=int） |
| 3 | 严重 | 功能 | 代码上传依赖 MinIO（本地/仿真环境不可用） |
| 4 | 严重 | 功能 | 多代码包时合规检查/导出崩溃 MultipleResultsFound |
| 5 | 严重 | 功能 | 导出任务合规检查参数不完整致永久失败 |
| 6 | 严重 | 功能 | 中文文件名下载 500（latin-1 编码错误） |
| 7 | 严重 | 功能 | 尼斯分类表无种子数据致商标功能不可用 |
| 9 | 严重 | 功能 | 登录/注册失败无错误反馈（store 闭包读旧值） |
| 1 | 轻微 | 噪音 | 每次加载页面GET /api/v1返回404 |
| 8 | 建议 | 交互 | 设置保存成功但无明确成功提示 |

### 问题详情

#### #2 [严重] 软著合规检查崩溃 500（None>=int）

- **预期**: 点击'执行合规检查'应返回规则结果
- **实际**: GET/POST /compliance/projects/{id}[/check] 返回500；_check_manual 第498行 page_count>=15 时 page_count 为 None 抛 TypeError
- **证据**: 后端traceback: compliance_checker.py:498 TypeError '>=' not supported between NoneType and int；生成草稿 word_count/page_count 未统计为 None

#### #3 [严重] 代码上传依赖 MinIO（本地/仿真环境不可用）

- **预期**: STORAGE_TYPE=local 时应使用本地文件系统存储
- **实际**: POST /code-bundles 返回500；storage_service.py 硬编码 Minio，忽略 STORAGE_TYPE=local/STORAGE_BASE_PATH，连接 localhost:9000 失败
- **证据**: 后端traceback: MaxRetryError localhost:9000 Connection refused

#### #4 [严重] 多代码包时合规检查/导出崩溃 MultipleResultsFound

- **预期**: 上传多个代码包后合规检查与导出应取最新包正常工作
- **实际**: compliance.py:127 与 job_runner.py:224 用 scalar_one_or_none() 查 CodeBundle，存在≥2包时抛 MultipleResultsFound → 500
- **证据**: 后端traceback: compliance.py:127 MultipleResultsFound；DB确认 code_bundle 2 行

#### #5 [严重] 导出任务合规检查参数不完整致永久失败

- **预期**: 导出任务的合规检查应与UI一致
- **实际**: job_runner.py 给 compliance_checker 传的 manual 字典缺 title/word_count、software_info 缺 functional_description，导致 MANUAL_001 标题检查永远 FAILED，导出永久无法通过
- **证据**: 对比：compliance API 可通过，job_runner 内部合规总失败；修复后导出 status=succeeded

#### #6 [严重] 中文文件名下载 500（latin-1 编码错误）

- **预期**: 下载含中文文件名的导出包应返回 zip
- **实际**: export_jobs download 用 filename=软著申请...放入 Content-Disposition 触发 UnicodeEncodeError latin-1 → 500
- **证据**: 后端traceback: export_jobs.py:177 UnicodeEncodeError latin-1; 6处下载端点均受影响

#### #7 [严重] 尼斯分类表无种子数据致商标功能不可用

- **预期**: 商标应可查询并选择尼斯分类
- **实际**: nice_classification 表为空(0行)，/nice-classes 返回空，合规'尼斯分类'规则永远失败，商标无法选择分类/导出
- **证据**: DB确认 nice_classification 0 行；新增 db/nice_seed.py 在启动时填充45类

#### #9 [严重] 登录/注册失败无错误反馈（store 闭包读旧值）

- **预期**: 登录密码错误/注册重复邮箱时应显示明确错误
- **实际**: use-auth.ts mutationFn 中 store.error 是渲染快照旧值，await store.login() 后仍为 null，导致 throw 不触发，登录页无任何错误反馈，用户不知为何登录失败
- **证据**: text-login-error 修复前不可见、修复后显示'用户名或密码错误'；修复用 useAuthStore.getState().error 读最新值

#### #1 [轻微] 每次加载页面GET /api/v1返回404

- **预期**: 不应有空路径探测
- **实际**: 每个页面加载都出现 GET /api/v1 → 404（控制台报错1条）
- **证据**: netFails: 404 http://localhost:3000/api/v1；不影响功能

#### #8 [建议] 设置保存成功但无明确成功提示

- **预期**: 保存个人信息后应有可见的成功反馈
- **实际**: PUT /auth/me 返回200且数据已持久化，但页面无明确'保存成功'toast（仅文案含'更新'）
- **证据**: auth响应 200；display_name 已更新但未见 toast

## 操作过程回放

| # | 动作 | 观察 | 判定 |
|---|---|---|---|
| 1 | 游客访问首页 | 落地页正常渲染：标题'一句话生成全套软著申请材料'、导航(首页/定价/帮助/登录/注册)、三大业务入口、无console错误、无网络失败 | ✅ pass |
| 2 | 进入注册页并完整填写表单 | 注册页含用户名/邮箱/昵称/密码/确认密码5字段，data-testid齐全；首次只填了密码未填确认密码导致未提交(前端校验生效，合理) | ✅ pass |
| 3 | 提交注册 | 注册成功，自动登录并跳转/dashboard工作台，侧边栏三大业务入口齐全(软著/专利/商标) | ✅ pass |
| 4 | 退出后用账号登录 | 登录页正常，提交后跳转/dashboard；工作台显示三大业务卡片+最近项目(暂无) | ✅ pass |
| 5 | 软著：填写业务描述并点击'开始生成 AI 草稿' | 生成任务 succeeded(progress=100)；自动产出软件信息(全称/开发语言Python·TypeScript/运行环境/功能描述/技术特征)与操作说明书(真实HTML：产品概述/功能模块/操作流程)；DB确认 source=ai | ✅ pass |
| 6 | 软著：完整生成+合规+导出+下载 | 全链路打通：生成succeeded→代码上传(4830行)→合规13规则10通过0失败→导出succeeded→下载200；导出zip有效(504b0304)含6文件(软件信息/代码/说明书/合规/申请表/对照表) | ✅ pass |
| 7 | 专利：创建项目→生成权利要求/说明书 | 生成 succeeded/draft_ready；产出真实内容：technical_field/background_art/invention_content(JSON)/implementation/abstract + 2条权利要求(独立+从属，'其特征在于...') | ✅ pass |
| 8 | 专利：导出+下载 | 导出 succeeded→下载200；zip(70575B)含说明书+权利要求书(TXT+DOCX各2份)；中文文件名下载已修复 | ✅ pass |
| 9 | 商标：创建→生成→尼斯分类推荐→合规→导出下载 | 全链路打通：生成succeeded且自动推荐尼斯分类(第35类广告销售/第42类网站服务含商品项目)；合规4规则全通过；导出succeeded→下载200；zip含商标注册申请书(TXT+DOCX) | ✅ pass |
| 10 | 配套页面渲染巡检(11页) | 工作台/所有项目/软著/专利/商标/订阅/组织/设置/规范/帮助均正常渲染无崩溃；管理后台对普通用户正确显示'无访问权限'；所有项目列表展示已建项目含进度与操作；设置页保存昵称成功(PUT /auth/me 200，display_name持久化) | ✅ pass |
| 11 | 边界/异常探索（空注册/超长名/重复邮箱/错误密码/XSS） | 空注册前端422拦截；超长名/特殊字符被拒；修复后错误密码显示'用户名或密码错误'、重复邮箱显示错误并留在注册页；XSS负载作为文本渲染未执行 | ✅ pass |

## 结论
⚠️ 发现 9 个问题，其中 7 个致命/严重，建议优先处理后再深入测试。
