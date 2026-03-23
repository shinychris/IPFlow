"""商标 AI 草稿生成服务."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ipflow.models import Project


@dataclass
class TrademarkDraftResult:
    trademark_info: dict[str, Any]
    nice_classes: list[dict[str, Any]]


class TrademarkAIGenerator:
    """根据项目信息生成商标草稿."""

    def generate(self, project: Project, inputs: dict[str, Any] | None = None) -> TrademarkDraftResult:
        payload = inputs or {}
        extra_brief = (payload.get("inputs", {}) or {}).get("extra_brief", "")
        trademark_name = project.name[:20]

        info = {
            "trademark_type": "word",
            "trademark_name": trademark_name,
            "description": extra_brief or f"{trademark_name} 作为品牌标识用于相关服务。",
            "design_description": None,
            "color_claim": None,
            "special_notes": "AI 草稿，可在详情页自由编辑。",
        }
        nice_classes = [
            {"class_number": 35, "goods_services": ["广告宣传", "商业管理辅助"]},
            {"class_number": 42, "goods_services": ["软件设计与开发", "技术咨询服务"]},
        ]
        return TrademarkDraftResult(trademark_info=info, nice_classes=nice_classes)
