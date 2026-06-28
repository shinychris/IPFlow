"""合规检查 API.

提供软著/专利/商标申请材料的合规检查功能。
根据项目类型（``project_type``）分发到对应的规则引擎。
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import (
    Project,
    CopyrightData,
    CodeBundle,
    CopyrightManual,
    PatentData,
    PatentClaim,
    TrademarkData,
    TrademarkNiceClass,
)
from ipflow.models.enums import ProjectType
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.services.copyright.compliance_checker import ComplianceChecker
from ipflow.services.compliance import (
    PatentComplianceChecker,
    TrademarkComplianceChecker,
)

router = APIRouter(prefix="/compliance", tags=["合规检查"])


def _enum_value(value: Any) -> Optional[str]:
    """安全获取枚举的字符串值.

    SQLModel 的枚举列在不同后端（Postgres 原生枚举 vs SQLite/MySQL 字符串）
    可能返回枚举成员或纯字符串；本函数统一规整为字符串。
    """
    if value is None:
        return None
    return getattr(value, "value", str(value))


async def _get_owned_project(
    db: AsyncSession, project_id: UUID, current_user: User
) -> Project:
    """加载并校验当前用户对项目的访问权限."""
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
    return project


def _serialize_report(report) -> dict:
    """将 ComplianceReport 序列化为接口响应."""
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


# =============================================================================
# 软著合规检查
# =============================================================================


async def _check_copyright(
    db: AsyncSession, project_id: UUID
) -> dict:
    """软著材料合规检查."""
    # 软件信息
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

    # 代码包（一个 copyright_data 可对应多个上传，取最新一条做合规评估）
    result = await db.execute(
        select(CodeBundle)
        .where(CodeBundle.copyright_data_id == copyright_data.id)
        .order_by(CodeBundle.created_at.desc())
        if copyright_data
        else select(CodeBundle).where(False)
    )
    code_bundle = result.scalars().first()
    code_bundle_info = None
    if code_bundle:
        code_bundle_info = {
            "total_files": code_bundle.total_files,
            "total_lines": code_bundle.total_lines,
            "has_enough_code": code_bundle.has_enough_code,
            "pages_data": code_bundle.pages_data,
        }

    # 说明书（可能存在多份，取最新一条做合规评估）
    result = await db.execute(
        select(CopyrightManual)
        .where(CopyrightManual.copyright_data_id == copyright_data.id)
        .order_by(CopyrightManual.created_at.desc())
        if copyright_data
        else select(CopyrightManual).where(False)
    )
    manual = result.scalars().first()
    manual_info = None
    if manual:
        manual_info = {
            "title": manual.title,
            "word_count": manual.word_count,
            "page_count": manual.page_count,
            "has_toc": manual.has_toc,
            "has_chapters": manual.has_chapters,
        }

    checker = ComplianceChecker()
    report = checker.check(
        project_id=project_id,
        software_info=software_info,
        code_bundle=code_bundle_info,
        manual=manual_info,
    )
    return _serialize_report(report)


# =============================================================================
# 专利合规检查
# =============================================================================


async def _check_patent(db: AsyncSession, project_id: UUID) -> dict:
    """专利材料合规检查."""
    # 专利基本信息
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()

    patent_info = None
    if patent_data:
        patent_info = {
            "title": patent_data.title,
            "abstract": patent_data.abstract,
            "patent_type": _enum_value(patent_data.patent_type),
        }

    # 说明书章节
    description = None
    if patent_data:
        description = {
            "technical_field": patent_data.technical_field,
            "background_art": patent_data.background_art,
            "problem_solved": (patent_data.invention_content or {}).get(
                "problem_solved"
            )
            if isinstance(patent_data.invention_content, dict)
            else None,
            "technical_solution": (patent_data.invention_content or {}).get(
                "technical_solution"
            )
            if isinstance(patent_data.invention_content, dict)
            else None,
            "beneficial_effects": (patent_data.invention_content or {}).get(
                "beneficial_effects"
            )
            if isinstance(patent_data.invention_content, dict)
            else None,
            "implementation": patent_data.implementation,
        }

    # 权利要求
    result = await db.execute(
        select(PatentClaim)
        .where(PatentClaim.patent_data_id == patent_data.id)
        .order_by(PatentClaim.claim_number)
        if patent_data
        else select(PatentClaim).where(False)
    )
    claims = [
        {
            "claim_number": c.claim_number,
            "claim_type": c.claim_type,
            "parent_claim_number": c.parent_claim_number,
            "content": c.content,
        }
        for c in result.scalars().all()
    ]

    checker = PatentComplianceChecker()
    report = checker.check(
        project_id=project_id,
        patent_info=patent_info,
        description=description,
        claims=claims,
    )
    return _serialize_report(report)


# =============================================================================
# 商标合规检查
# =============================================================================


async def _check_trademark(db: AsyncSession, project_id: UUID) -> dict:
    """商标材料合规检查."""
    result = await db.execute(
        select(TrademarkData).where(TrademarkData.project_id == project_id)
    )
    trademark_data = result.scalar_one_or_none()

    trademark_info = None
    if trademark_data:
        trademark_info = {
            "trademark_name": trademark_data.trademark_name,
            "trademark_type": _enum_value(trademark_data.trademark_type),
            "color_claim": trademark_data.color_claim,
            "design_description": trademark_data.design_description,
            "upload_id": str(trademark_data.upload_id)
            if trademark_data.upload_id
            else None,
        }

    # 尼斯分类
    result = await db.execute(
        select(TrademarkNiceClass).where(
            TrademarkNiceClass.trademark_data_id == trademark_data.id
        )
        if trademark_data
        else select(TrademarkNiceClass).where(False)
    )
    nice_classes = [
        {
            "goods_services": nc.goods_services or [],
        }
        for nc in result.scalars().all()
    ]

    checker = TrademarkComplianceChecker()
    report = checker.check(
        project_id=project_id,
        trademark_info=trademark_info,
        nice_classes=nice_classes,
    )
    return _serialize_report(report)


# =============================================================================
# API 端点
# =============================================================================


async def _run_check(
    db: AsyncSession, project_id: UUID, current_user: User
) -> dict:
    """根据项目类型分发到对应合规检查."""
    project = await _get_owned_project(db, project_id, current_user)

    if project.project_type == ProjectType.COPYRIGHT:
        return await _check_copyright(db, project_id)
    elif project.project_type == ProjectType.PATENT:
        return await _check_patent(db, project_id)
    elif project.project_type == ProjectType.TRADEMARK:
        return await _check_trademark(db, project_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的项目类型: {project.project_type}",
        )


@router.get("/projects/{project_id}")
async def get_compliance_check(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取项目合规检查结果（按项目类型自动分发）."""
    return await _run_check(db, project_id, current_user)


@router.post("/projects/{project_id}/check")
async def run_compliance_check(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """执行合规检查（按项目类型自动分发）."""
    return await _run_check(db, project_id, current_user)
