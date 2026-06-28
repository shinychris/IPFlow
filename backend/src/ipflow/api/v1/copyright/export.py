"""导出 API.

提供软著申请材料导出功能。
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import Project, CopyrightData, CodeBundle, CopyrightManual
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.core.content_disposition import build_content_disposition
from ipflow.services.copyright.export_generator import (
    ExportGenerator,
    ExportConfig,
)

router = APIRouter()


@router.post("/export")
async def export_project(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """导出软著申请材料包.
    
    生成包含所有申请材料的 ZIP 文件。
    """
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
    
    if not copyright_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先填写软件信息",
        )
    
    # 获取代码包
    result = await db.execute(
        select(CodeBundle).where(
            CodeBundle.copyright_data_id == copyright_data.id
        )
    )
    code_bundle = result.scalar_one_or_none()
    
    if not code_bundle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传源代码",
        )
    
    # 获取说明书
    result = await db.execute(
        select(CopyrightManual).where(
            CopyrightManual.copyright_data_id == copyright_data.id
        )
    )
    manual = result.scalar_one_or_none()
    
    # 准备导出配置
    config = ExportConfig(
        software_name=copyright_data.software_full_name,
        version=copyright_data.version_number,
        applicant_name=project.subject_name or current_user.username,
        completion_date=project.completion_date.isoformat() if project.completion_date else datetime.now().strftime("%Y-%m-%d"),
        first_publication_date=project.first_publication_date.isoformat() if project.first_publication_date else None,
    )
    
    # 准备软件信息
    software_info = {
        "software_full_name": copyright_data.software_full_name,
        "software_short_name": copyright_data.software_short_name,
        "version_number": copyright_data.version_number,
        "development_language": copyright_data.development_language,
        "development_environment": copyright_data.development_environment,
        "runtime_environment": copyright_data.runtime_environment,
        "code_line_count": copyright_data.code_line_count,
        "functional_description": copyright_data.functional_description or "",
        "technical_features": copyright_data.technical_features or "",
        "target_domain": copyright_data.target_domain,
    }
    
    # 准备说明书
    manual_info = None
    if manual:
        manual_info = {
            "title": manual.title,
            "content_html": manual.content_html or "",
        }
    
    # 生成导出包
    generator = ExportGenerator()
    export_result = generator.generate_export_package(
        config=config,
        software_info=software_info,
        code_pages=code_bundle.pages_data,
        manual=manual_info,
    )
    
    # 更新项目状态
    from ipflow.models import ProjectStatus
    project.status = ProjectStatus.PENDING_SUBMIT
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    # 返回文件流
    return StreamingResponse(
        iter([export_result.content]),
        media_type="application/zip",
        headers={
            "Content-Disposition": build_content_disposition(export_result.file_name),
            "Content-Length": str(export_result.file_size),
        },
    )


@router.get("/export/preview")
async def preview_export(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """预览导出内容.
    
    返回导出包的预览信息，不生成文件。
    """
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
    
    # 获取代码包
    code_bundle = None
    if copyright_data:
        result = await db.execute(
            select(CodeBundle).where(
                CodeBundle.copyright_data_id == copyright_data.id
            )
        )
        code_bundle = result.scalar_one_or_none()
    
    # 获取说明书
    manual = None
    if copyright_data:
        result = await db.execute(
            select(CopyrightManual).where(
                CopyrightManual.copyright_data_id == copyright_data.id
            )
        )
        manual = result.scalar_one_or_none()
    
    return {
        "software_info": {
            "has_data": copyright_data is not None,
            "software_name": copyright_data.software_full_name if copyright_data else None,
        },
        "code_bundle": {
            "has_data": code_bundle is not None,
            "total_pages": len(code_bundle.pages_data) if code_bundle else 0,
            "has_enough_code": code_bundle.has_enough_code if code_bundle else False,
        },
        "manual": {
            "has_data": manual is not None,
            "page_count": manual.page_count if manual else 0,
        },
        "files_in_package": [
            "01_软件信息.txt",
            "02_源代码_鉴别材料.txt",
            "03_操作说明书.txt",
            "04_材料清单.txt",
            "05_打印指南.txt",
            "06_网报对照表.txt",
        ],
    }
