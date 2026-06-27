# 软著 AI 自动生成流程测试清单

## 1. 接口链路验证

- 创建软著项目后，`flow_status` 初始值应为 `draft_pending`。
- 访问 `GET /api/v1/copyright/projects/{project_id}/generation-context` 返回基础信息与能力标记。
- 调用 `POST /api/v1/copyright/projects/{project_id}/generation-jobs` 后应返回任务 ID，任务状态最终变为 `succeeded` 或 `failed`。
- 调用 `GET /api/v1/copyright/generation-jobs/{job_id}` 能获取进度、错误、产物信息。
- 调用 `POST /api/v1/copyright/projects/{project_id}/materials/confirm` 后，软著草稿应标记为 `is_confirmed=true`。
- 调用 `POST /api/v1/copyright/projects/{project_id}/export-jobs` 后可通过 `GET /api/v1/copyright/export-jobs/{job_id}` 查询结果并下载。

## 2. 页面路由验证

- `project/new` 创建软著项目后，应跳转至 `/project/{id}/copyright/generate`。
- 引导页提交后应回到 `/project/{id}` 并看到流程/任务状态信息。
- 项目卡片在 `draft_pending|generating` 状态下应优先跳转生成引导页。
- 详情页显示最近生成任务与导出任务状态。

## 3. 数据一致性验证

- AI 生成后 `copyright_data.source` 与 `copyright_manual.source` 应更新为 `ai` 或 `mixed`。
- 人工编辑软件信息/说明书后，`revision` 自动递增，`is_confirmed` 自动回退为 `false`。
- 任务失败时应有 `error_message`，并且项目状态不应进入 `export_ready`。

## 4. 验收指标

- 创建项目到可编辑草稿的耗时：目标 <= 2 分钟。
- 导出任务成功率：目标 >= 95%。
- 失败任务重试成功率：目标 >= 80%。
- 人工确认内容被 AI 覆盖率：目标 = 0（默认 `fill_blank_only`）。
