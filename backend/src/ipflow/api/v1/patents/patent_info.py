"""专利信息 API.

提供专利基本信息的获取和更新接口。
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import PatentData, Project, ProjectType, PatentType, PatentStatus
from ipflow.models.user import User
from ipflow.api.deps import require_active_user

router = APIRouter()


# =============================================================================
# 请求/响应模型
# =============================================================================


class PatentInfoBase(BaseModel):
    """专利信息基础模型."""
    
    patent_type: PatentType = Field(..., description="专利类型")
    title: str = Field(..., min_length=1, max_length=200, description="专利名称")
    technical_field: Optional[str] = Field(None, description="技术领域")
    background_art: Optional[str] = Field(None, description="背景技术")
    abstract: Optional[str] = Field(None, description="摘要")
    abstract_figure_number: Optional[str] = Field(None, max_length=10, description="摘要附图编号")


class PatentInfoCreate(PatentInfoBase):
    """创建专利信息请求."""
    pass


class PatentInfoUpdate(BaseModel):
    """更新专利信息请求."""
    
    patent_type: Optional[PatentType] = None
    title: Optional[str] = Field(None, max_length=200)
    technical_field: Optional[str] = None
    background_art: Optional[str] = None
    abstract: Optional[str] = None
    abstract_figure_number: Optional[str] = Field(None, max_length=10)


class PatentInfoResponse(PatentInfoBase):
    """专利信息响应."""
    
    id: UUID
    project_id: UUID
    status: PatentStatus
    claims_count: int
    drawings_count: int
    application_number: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# =============================================================================
# API 端点
# =============================================================================


@router.get("/patent-info", response_model=dict)
async def get_patent_info(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取专利信息.
    
    获取指定专利项目的详细信息。
    """
    # 验证项目存在且属于当前用户
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
    
    # 查询专利信息
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
        "project_id": str(patent_data.project_id),
        "patent_type": patent_data.patent_type.value,
        "title": patent_data.title,
        "technical_field": patent_data.technical_field,
        "background_art": patent_data.background_art,
        "abstract": patent_data.abstract,
        "abstract_figure_number": patent_data.abstract_figure_number,
        "status": patent_data.status.value,
        "claims_count": patent_data.claims_count,
        "drawings_count": patent_data.drawings_count,
        "application_number": patent_data.application_number,
        "source": patent_data.source,
        "revision": patent_data.revision,
        "is_confirmed": patent_data.is_confirmed,
        "last_edited_by": str(patent_data.last_edited_by) if patent_data.last_edited_by else None,
        "created_at": patent_data.created_at.isoformat(),
        "updated_at": patent_data.updated_at.isoformat(),
    }


@router.put("/patent-info", response_model=dict)
async def update_patent_info(
    project_id: UUID,
    data: PatentInfoBase,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新专利信息.
    
    创建或更新专利项目的详细信息。
    """
    from datetime import datetime
    
    # 验证项目存在且属于当前用户
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
    
    # 查询是否已存在专利信息
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    if patent_data:
        # 更新现有记录
        patent_data.patent_type = data.patent_type
        patent_data.title = data.title
        patent_data.technical_field = data.technical_field
        patent_data.background_art = data.background_art
        patent_data.abstract = data.abstract
        patent_data.abstract_figure_number = data.abstract_figure_number
        patent_data.source = "human"
        patent_data.revision += 1
        patent_data.is_confirmed = False
        patent_data.last_edited_by = current_user.id
        patent_data.updated_at = datetime.utcnow()
    else:
        # 创建新记录
        patent_data = PatentData(
            project_id=project_id,
            patent_type=data.patent_type,
            title=data.title,
            technical_field=data.technical_field,
            background_art=data.background_art,
            abstract=data.abstract,
            abstract_figure_number=data.abstract_figure_number,
            source="human",
            revision=1,
            is_confirmed=False,
            last_edited_by=current_user.id,
        )
        db.add(patent_data)
    
    await db.commit()
    await db.refresh(patent_data)
    
    # 更新项目
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "id": str(patent_data.id),
        "project_id": str(patent_data.project_id),
        "patent_type": patent_data.patent_type.value,
        "title": patent_data.title,
        "technical_field": patent_data.technical_field,
        "background_art": patent_data.background_art,
        "abstract": patent_data.abstract,
        "abstract_figure_number": patent_data.abstract_figure_number,
        "status": patent_data.status.value,
        "claims_count": patent_data.claims_count,
        "drawings_count": patent_data.drawings_count,
        "application_number": patent_data.application_number,
        "source": patent_data.source,
        "revision": patent_data.revision,
        "is_confirmed": patent_data.is_confirmed,
        "last_edited_by": str(patent_data.last_edited_by) if patent_data.last_edited_by else None,
        "created_at": patent_data.created_at.isoformat(),
        "updated_at": patent_data.updated_at.isoformat(),
    }


@router.get("/patent-info/status", response_model=dict)
async def get_patent_status(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取专利状态."""
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
    
    # 查询专利信息
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    if not patent_data:
        return {
            "has_data": False,
            "status": None,
        }
    
    return {
        "has_data": True,
        "status": patent_data.status.value,
        "application_number": patent_data.application_number,
        "publication_number": patent_data.publication_number,
        "grant_number": patent_data.grant_number,
        "claims_count": patent_data.claims_count,
        "drawings_count": patent_data.drawings_count,
    }
