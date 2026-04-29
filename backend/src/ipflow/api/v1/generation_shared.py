"""材料生成 API 共用片段（generation-context 等）."""

from __future__ import annotations

from typing import Any

from ipflow.models import Project


def base_profile_for_generation(project: Project) -> dict[str, Any]:
    """各业务线 generation-context 中 base_profile 的统一形状（供前端预填展示）."""
    st = project.subject_type
    st_val = st.value if st is not None and hasattr(st, "value") else None
    return {
        "name": project.name,
        "version": project.version,
        "description": project.description,
        "subject_name": project.subject_name,
        "subject_type": st_val,
        "development_method": project.development_method,
        "publication_status": project.publication_status,
        "completion_date": project.completion_date.isoformat()
        if project.completion_date
        else None,
        "first_publication_date": project.first_publication_date.isoformat()
        if project.first_publication_date
        else None,
    }
