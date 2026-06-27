"""Agent 草稿后端基类与结构化输出模型.

提供 pydantic-ai ``Agent`` 的通用构建与运行逻辑。三类业务（软著/专利/商标）
各自的 provider 只需：提供技能（SKILL.md）路径、结构化输出模型类、
以及把结构化结果转成各自 ``DraftResult`` 的方法。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent

from ipflow.config import Settings, get_settings
from ipflow.services.agent.models import AgentModelUnavailable, build_agent_model

logger = logging.getLogger(__name__)

OutputT = TypeVar("OutputT", bound=BaseModel)


def load_skill_instructions(skill_path: Path) -> str:
    """读取技能 SKILL.md 全文作为 Agent 系统提示词。

    Args:
        skill_path: SKILL.md 的绝对路径

    Returns:
        SKILL.md 全文；文件不存在时返回空串（不抛异常，由上层决定是否回退）
    """
    try:
        text = skill_path.read_text(encoding="utf-8")
        return text
    except FileNotFoundError:
        logger.warning("Agent 技能文件不存在：%s", skill_path)
        return ""
    except OSError as e:
        logger.warning("读取 Agent 技能文件失败 %s：%s", skill_path, e)
        return ""


class BaseAgentDraftProvider(Generic[OutputT]):
    """基于 pydantic-ai 的草稿生成 provider 基类。

    子类需设置类属性 ``output_model``（pydantic 结构化输出类型）与
    ``instructions_prefix``，并实现 ``build_user_prompt`` 与
    ``to_draft_result``。``generate`` 为 async，可直接在 async 任务里 await。
    """

    #: 结构化输出模型（pydantic BaseModel），由子类指定
    output_model: Type[BaseModel] = BaseModel

    #: 生成指令前缀（置于技能 SKILL.md 之前）
    instructions_prefix: str = "你是知识产权申报材料撰写助手。"

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    # ------------------------------------------------------------------
    # 子类必须实现
    # ------------------------------------------------------------------
    def get_skill_path(self) -> Path:
        """返回该业务对应的 SKILL.md 路径。"""
        raise NotImplementedError

    def build_user_prompt(self, project: Any, inputs: dict[str, Any]) -> str:
        """根据项目与输入构造用户提示词。"""
        raise NotImplementedError

    def to_draft_result(self, output: OutputT, project: Any) -> Any:
        """把结构化输出转成业务 DraftResult。"""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 运行
    # ------------------------------------------------------------------
    def _build_agent(self) -> Agent:
        """构建 pydantic-ai Agent（惰性，每次 generate 重建以反映最新配置）。"""
        model_name = build_agent_model(self._settings)
        skill_text = load_skill_instructions(self.get_skill_path())
        # 指令 = 前缀 + 技能全文（技能即「skill」调用）
        instructions = (
            f"{self.instructions_prefix}\n\n{skill_text}"
            if skill_text
            else self.instructions_prefix
        ).strip()
        return Agent(
            model=model_name,
            output_type=self.output_model,
            instructions=instructions,
        )

    async def generate(self, project: Any, inputs: dict[str, Any]) -> Any:
        """运行 Agent 生成草稿。

        失败（模型不可用 / 运行异常）时抛出，由 ``provider_invoke`` 决定是否回退 template。

        Raises:
            AgentModelUnavailable: 模型/凭证不可用
            Exception: Agent 运行期错误
        """
        agent = self._build_agent()
        user_prompt = self.build_user_prompt(project, inputs)
        result = await agent.run(user_prompt)
        return self.to_draft_result(result.output, project)
