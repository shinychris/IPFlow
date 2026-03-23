"""跨业务类型的材料生成辅助（源码目录、provider 调用）."""

from ipflow.services.generation.code_root import fetch_code_root_for_job
from ipflow.services.generation.provider_invoke import invoke_material_draft_provider

__all__ = ["fetch_code_root_for_job", "invoke_material_draft_provider"]
