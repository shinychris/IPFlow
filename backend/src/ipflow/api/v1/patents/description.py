"""说明书 API.

提供专利说明书的获取和更新接口。
"""

from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import PatentData, Project, ProjectType
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.utils.enums import enum_value

router = APIRouter()


# =============================================================================
# 请求/响应模型
# =============================================================================


class InventionContent(BaseModel):
    """发明内容模型."""
    
    problem_solved: Optional[str] = Field(None, description="要解决的技术问题")
    technical_solution: Optional[str] = Field(None, description="技术方案")
    beneficial_effects: Optional[str] = Field(None, description="有益效果")


class DescriptionBase(BaseModel):
    """说明书基础模型."""
    
    technical_field: Optional[str] = Field(None, description="技术领域")
    background_art: Optional[str] = Field(None, description="背景技术")
    invention_content: Optional[InventionContent] = Field(None, description="发明内容")
    implementation: Optional[str] = Field(None, description="具体实施方式")


class DescriptionUpdate(BaseModel):
    """更新说明书请求."""
    
    technical_field: Optional[str] = None
    background_art: Optional[str] = None
    invention_content: Optional[InventionContent] = None
    implementation: Optional[str] = None


# =============================================================================
# API 端点
# =============================================================================


@router.get("/description", response_model=dict)
async def get_description(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取说明书内容.
    
    获取指定专利项目的说明书内容。
    """
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.PATENT,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取专利数据
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    if not patent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专利信息不存在",
        )
    
    return {
        "id": str(patent_data.id),
        "project_id": str(project_id),
        "technical_field": patent_data.technical_field,
        "background_art": patent_data.background_art,
        "invention_content": patent_data.invention_content or {
            "problem_solved": None,
            "technical_solution": None,
            "beneficial_effects": None,
        },
        "implementation": patent_data.implementation,
        "updated_at": patent_data.updated_at.isoformat(),
    }


@router.put("/description", response_model=dict)
async def update_description(
    project_id: UUID,
    data: DescriptionBase,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新说明书内容.
    
    更新指定专利项目的说明书内容。
    """
    from datetime import datetime
    
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.PATENT,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取专利数据
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    if not patent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专利信息不存在",
        )
    
    # 更新字段
    if data.technical_field is not None:
        patent_data.technical_field = data.technical_field
    if data.background_art is not None:
        patent_data.background_art = data.background_art
    if data.invention_content is not None:
        patent_data.invention_content = data.invention_content.model_dump()
    if data.implementation is not None:
        patent_data.implementation = data.implementation
    
    patent_data.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(patent_data)
    
    return {
        "id": str(patent_data.id),
        "project_id": str(project_id),
        "technical_field": patent_data.technical_field,
        "background_art": patent_data.background_art,
        "invention_content": patent_data.invention_content or {
            "problem_solved": None,
            "technical_solution": None,
            "beneficial_effects": None,
        },
        "implementation": patent_data.implementation,
        "updated_at": patent_data.updated_at.isoformat(),
    }


@router.get("/description/preview", response_model=dict)
async def preview_description(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """预览完整说明书.
    
    生成完整的说明书预览文本。
    """
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.PATENT,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取专利数据
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    if not patent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专利信息不存在",
        )
    
    # 生成预览文本
    sections = []
    
    # 技术领域
    if patent_data.technical_field:
        sections.append(f"技术领域\n\n{patent_data.technical_field}")
    
    # 背景技术
    if patent_data.background_art:
        sections.append(f"背景技术\n\n{patent_data.background_art}")
    
    # 发明内容
    if patent_data.invention_content:
        content_parts = []
        if patent_data.invention_content.get("problem_solved"):
            content_parts.append(f"要解决的技术问题:\n{patent_data.invention_content['problem_solved']}")
        if patent_data.invention_content.get("technical_solution"):
            content_parts.append(f"技术方案:\n{patent_data.invention_content['technical_solution']}")
        if patent_data.invention_content.get("beneficial_effects"):
            content_parts.append(f"有益效果:\n{patent_data.invention_content['beneficial_effects']}")
        if content_parts:
            sections.append("发明内容\n\n" + "\n\n".join(content_parts))
    
    # 具体实施方式
    if patent_data.implementation:
        sections.append(f"具体实施方式\n\n{patent_data.implementation}")
    
    full_text = "\n\n".join(sections) if sections else "说明书内容为空"
    
    return {
        "project_id": str(project_id),
        "title": patent_data.title,
        "patent_type": enum_value(patent_data.patent_type),
        "full_text": full_text,
        "sections_count": len(sections),
        "has_complete_content": len(sections) >= 3,  # 至少包含技术领域、背景技术、发明内容
    }
