# 开发日志：pydantic-ai Agent 后端集成

> **日期**: 2026-06-27
> **任务**: agent 采用 pydantic-ai 框架，支持 skill 调用（software-copyright-application）
> **基线**: commit e17d4ff（第三轮整改）

## 背景

软著/专利/商标草稿生成此前有三个后端：`template`（模板）、`claude_code`（外部 Claude CLI）、`llm`（通用 LLM）。本次按需求「agent 采用 pydantic-ai 框架，支持 skill 调用」新增第 4 个后端 `agent`，以技能 SKILL.md 作为 Agent 系统提示词，通过 pydantic-ai 结构化输出约束返回 JSON。

## 架构决策（已与用户确认）
- 新增 `agent` 后端，与现有三个并存；默认仍 `template`，需显式 `*_DRAFT_BACKEND=agent` 启用。
- 复用现有 `AI_PROVIDER`/`AI_MODEL`/`OPENAI_API_KEY`/`ANTHROPIC_API_KEY`/`OLLAMA_BASE_URL`，按值映射 pydantic-ai 模型（openai/anthropic/ollama）。

## 实现内容

### 新增 `src/ipflow/services/agent/`
| 文件 | 职责 |
|------|------|
| `models.py` | `build_agent_model()`：按 AI_PROVIDER 返回 `"<provider>:<model>"` 字符串（pydantic-ai 自动解析+读凭证）；缺凭证抛 `AgentModelUnavailable`（触发回退） |
| `base.py` | `BaseAgentDraftProvider`：通用 pydantic-ai Agent 构建（SKILL.md 作 instructions + `output_type` 结构化）+ `async generate()` |
| `copyright_agent.py` | `CopyrightAgentDraftProvider`：软著 SKILL + CopyrightDraftOutput → DraftResult |
| `patent_agent.py` | `PatentAgentDraftProvider`：专利 SKILL + PatentDraftOutput → PatentDraftResult |
| `trademark_agent.py` | `TrademarkAgentDraftProvider`：商标 SKILL + TrademarkDraftOutput → TrademarkDraftResult |

### 接入与改造
- 3 个 `draft_providers.py` 工厂新增 `if backend == "agent"` 分支（惰性导入避免硬依赖）。
- `generation/provider_invoke.py`：新增 `agent` 的 **async 原生**调用路径（`await provider.generate()`，无需线程桥接）；agent/claude_code 失败时回退模板。
- `config.py`：三个 `*_DRAFT_BACKEND` description 补充 `agent`；fallback 注释更新。
- `pyproject.toml`：新增 `pydantic-ai>=2.0.0`。
- `api/v1/ai_config.py`：新增 `GET /ai/agent` 就绪探测端点。

### 技能同步
- 把外部 `/Users/chris/.cc-switch/skills/software-copyright-application/`（新版 423 行 SKILL.md + scripts/references/assets）同步进仓库 `backend/resources/skills/software-copyright-application/`，作为 agent 的权威技能源。

### pydantic-ai 2.0 API 适配
实测 pydantic-ai 2.0.0 与文档略有差异，已按实际版本实现：
- `Agent(model, output_type=..., instructions=...)`（2.0 用 `output_type` 非 `result_type`）。
- 模型类：`OpenAIChatModel`/`AnthropicModel`/`OllamaModel`（非 `OpenAIModel`）。
- 采用最稳的「提供商前缀模型名」字符串（如 `openai:gpt-4o`），框架自动读凭证，避免与 SDK 客户端构造耦合。

### 测试
- 新增 `tests/unit/test_agent_provider.py`（**18 个单测**）：build_agent_model 凭证校验、技能加载、3 类结构化输出转换、TestModel 端到端运行（零真实 API）、工厂集成、缺凭证回退。
- 使用 pydantic-ai `TestModel` 注入 + monkeypatch，无任何真实 LLM 调用。

## 验证（全绿）
| 验证项 | 结果 |
|--------|------|
| 后端 pytest 全量 | ✅ **222 passed**（204 + 18 新） |
| Agent 冒烟（无凭证） | ✅ 正确抛 AgentModelUnavailable（回退生效） |
| Agent 冒烟（TestModel） | ✅ 返回合法 DraftResult，prompt 含 SKILL.md |
| 路由数 | 128（+1 `/ai/agent`） |

## 已知限制
- 默认后端不变（template）；agent 需配置 AI 凭证才真正调用 LLM，否则回退 template（安全可用）。
- 专利/商标 `_patent_from_structured` 经 `__init__.py` 链存在**遗留循环导入**（与本任务无关），导致相关单测单独运行时报循环导入；在完整 pytest 套件（先加载 app）中不受影响，222 全过。建议后续清理该循环。
