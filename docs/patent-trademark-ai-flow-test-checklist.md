# 专利与商标 AI 流程测试清单

## 1. 专利链路

- 新建专利项目后跳转到 `/project/{id}/patent/generate`。
- 生成页点击“开始生成”后，`generation-jobs` 状态可查询并最终完成。
- 详情页可自由编辑：专利信息、说明书字段、权利要求可新增/删除。
- 点击“确认专利材料”后，专利数据 `is_confirmed` 为 `true`。
- 导出走 `export-jobs`：创建任务 -> 查询状态 -> 下载链接下载成功。

## 2. 商标链路

- 新建商标项目后跳转到 `/project/{id}/trademark/generate`。
- 生成页点击“开始生成”后，商标信息与推荐分类可在详情页编辑。
- 详情页可自由编辑：商标信息、尼斯分类可新增/删除。
- 点击“确认商标材料”后，商标数据 `is_confirmed` 为 `true`。
- 导出走 `export-jobs`：创建任务 -> 查询状态 -> 下载链接下载成功。

## 3. 统一交互

- 项目卡片（软著/专利/商标）均展示“详情”和“生成”按钮。
- 详情页顶部在三种类型下都可见“生成材料”入口。
- 任务失败时前端可见失败提示，且可重试触发生成或导出。

## 4. 类型与一致性

- 前后端商标类型枚举一致：`word/device/composite/3d/sound/color`。
- 任务表字段支持跨类型：`project_type`、`job_domain`。
- 专利/商标实体支持草稿治理字段：`source`、`revision`、`is_confirmed`、`last_edited_by`。
