"""向后兼容：请优先使用 generation_repo。"""

from ipflow.schemas.generation_repo import RepoInput, parse_repo_input_from_payload

__all__ = ["RepoInput", "parse_repo_input_from_payload"]
