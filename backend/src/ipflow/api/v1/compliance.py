"""合规检查 API.

提供合规检查功能。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import Project, CopyrightData, CodeBundle, CopyrightManual
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.services.copyright.compliance_checker import ComplianceChecker

router = APIRouter(prefix="/compliance", tags=["合规检查"])


@router.get("/projects/{project_id}")
async def get_compliance_check(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取项目合规检查结果."""
    # 验证项目权限
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取软件信息
    result = await db.execute(
        select(CopyrightData).where(CopyrightData.project_id == project_id)
    )
    copyright_data = result.scalar_one_or_none()
    
    software_info = None
    if copyright_data:
        software_info = {
            "software_full_name": copyright_data.software_full_name,
            "software_short_name": copyright_data.software_short_name,
            "version_number": copyright_data.version_number,
            "development_language": copyright_data.development_language,
            "development_environment": copyright_data.development_environment,
            "runtime_environment": copyright_data.runtime_environment,
            "code_line_count": copyright_data.code_line_count,
            "functional_description": copyright_data.functional_description,
            "technical_features": copyright_data.technical_features,
            "target_domain": copyright_data.target_domain,
        }
    
    # 获取代码包
    result = await db.execute(
        select(CodeBundle).where(
            CodeBundle.copyright_data_id == copyright_data.id
        ) if copyright_data else select(CodeBundle).where(False)
    )
    code_bundle = result.scalar_one_or_none()
    
    code_bundle_info = None
    if code_bundle:
        code_bundle_info = {
            "total_files": code_bundle.total_files,
            "total_lines": code_bundle.total_lines,
            "has_enough_code": code_bundle.has_enough_code,
            "pages_data": code_bundle.pages_data,
        }
    
    # 获取说明书
    result = await db.execute(
        select(CopyrightManual).where(
            CopyrightManual.copyright_data_id == copyright_data.id
        ) if copyright_data else select(CopyrightManual).where(False)
    )
    manual = result.scalar_one_or_none()
    
    manual_info = None
    if manual:
        manual_info = {
            "title": manual.title,
            "word_count": manual.word_count,
            "page_count": manual.page_count,
            "has_toc": manual.has_toc,
            "has_chapters": manual.has_chapters,
        }
    
    # 执行合规检查
    checker = ComplianceChecker()
    report = checker.check(
        project_id=project_id,
        software_info=software_info,
        code_bundle=code_bundle_info,
        manual=manual_info,
    )
    
    return {
        "project_id": str(report.project_id),
        "total_rules": report.total_rules,
        "passed": report.passed,
        "warnings": report.warnings,
        "failed": report.failed,
        "overall_status": report.overall_status.value,
        "can_export": report.can_export,
        "results": [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category.value,
                "status": r.status.value,
                "message": r.message,
                "suggestion": r.suggestion,
            }
            for r in report.results
        ],
    }


@router.post("/projects/{project_id}/check")
async def run_compliance_check(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """执行合规检查."""
    # 与 GET 接口相同，但明确触发检查
    return await get_compliance_check(project_id, current_user, db)
