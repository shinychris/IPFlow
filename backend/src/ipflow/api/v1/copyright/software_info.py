"""软著软件信息 API.

提供软件信息的获取和更新接口。
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import CopyrightData, Project, ProjectType
from ipflow.models.user import User
from ipflow.api.deps import require_active_user

router = APIRouter()


# =============================================================================
# 请求/响应模型
# =============================================================================


class SoftwareInfoBase(BaseModel):
    """软件信息基础模型."""
    
    software_full_name: str = Field(..., min_length=1, max_length=100)
    software_short_name: Optional[str] = Field(None, max_length=50)
    version_number: str = Field(..., max_length=20)
    development_language: str = Field(..., max_length=100)
    development_environment: Optional[str] = None
    runtime_environment: Optional[str] = None
    code_line_count: Optional[int] = None
    functional_description: Optional[str] = None
    technical_features: Optional[str] = None
    target_domain: Optional[str] = Field(None, max_length=100)


class SoftwareInfoCreate(SoftwareInfoBase):
    """创建软件信息请求."""
    pass


class SoftwareInfoUpdate(BaseModel):
    """更新软件信息请求."""
    
    software_full_name: Optional[str] = Field(None, max_length=100)
    software_short_name: Optional[str] = Field(None, max_length=50)
    version_number: Optional[str] = Field(None, max_length=20)
    development_language: Optional[str] = Field(None, max_length=100)
    development_environment: Optional[str] = None
    runtime_environment: Optional[str] = None
    code_line_count: Optional[int] = None
    functional_description: Optional[str] = None
    technical_features: Optional[str] = None
    target_domain: Optional[str] = Field(None, max_length=100)


class SoftwareInfoResponse(SoftwareInfoBase):
    """软件信息响应."""
    
    id: UUID
    project_id: UUID
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# =============================================================================
# API 端点
# =============================================================================


@router.get("/software-info", response_model=dict)
async def get_software_info(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取软件信息.
    
    获取指定软著项目的软件详细信息。
    """
    # 验证项目存在且属于当前用户
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.COPYRIGHT,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 查询软件信息
    result = await db.execute(
        select(CopyrightData).where(CopyrightData.project_id == project_id)
    )
    copyright_data = result.scalar_one_or_none()
    
    if not copyright_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="软件信息不存在",
        )
    
    return {
        "id": str(copyright_data.id),
        "project_id": str(copyright_data.project_id),
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
        "source": copyright_data.source,
        "revision": copyright_data.revision,
        "is_confirmed": copyright_data.is_confirmed,
        "last_edited_by": str(copyright_data.last_edited_by) if copyright_data.last_edited_by else None,
        "created_at": copyright_data.created_at.isoformat(),
        "updated_at": copyright_data.updated_at.isoformat(),
    }


@router.put("/software-info", response_model=dict)
async def update_software_info(
    project_id: UUID,
    data: SoftwareInfoBase,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新软件信息.
    
    创建或更新软著项目的软件详细信息。
    """
    from datetime import datetime
    
    # 验证项目存在且属于当前用户
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.COPYRIGHT,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 查询是否已存在软件信息
    result = await db.execute(
        select(CopyrightData).where(CopyrightData.project_id == project_id)
    )
    copyright_data = result.scalar_one_or_none()
    
    if copyright_data:
        # 更新现有记录
        copyright_data.software_full_name = data.software_full_name
        copyright_data.software_short_name = data.software_short_name
        copyright_data.version_number = data.version_number
        copyright_data.development_language = data.development_language
        copyright_data.development_environment = data.development_environment
        copyright_data.runtime_environment = data.runtime_environment
        copyright_data.code_line_count = data.code_line_count
        copyright_data.functional_description = data.functional_description
        copyright_data.technical_features = data.technical_features
        copyright_data.target_domain = data.target_domain
        copyright_data.source = "human"
        copyright_data.revision += 1
        copyright_data.is_confirmed = False
        copyright_data.last_edited_by = current_user.id
        copyright_data.updated_at = datetime.utcnow()
    else:
        # 创建新记录
        copyright_data = CopyrightData(
            project_id=project_id,
            software_full_name=data.software_full_name,
            software_short_name=data.software_short_name,
            version_number=data.version_number,
            development_language=data.development_language,
            development_environment=data.development_environment,
            runtime_environment=data.runtime_environment,
            code_line_count=data.code_line_count,
            functional_description=data.functional_description,
            technical_features=data.technical_features,
            target_domain=data.target_domain,
            source="human",
            revision=1,
            is_confirmed=False,
            last_edited_by=current_user.id,
        )
        db.add(copyright_data)
    
    await db.commit()
    await db.refresh(copyright_data)
    
    # 更新项目的版本号
    project.version = data.version_number
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "id": str(copyright_data.id),
        "project_id": str(copyright_data.project_id),
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
        "source": copyright_data.source,
        "revision": copyright_data.revision,
        "is_confirmed": copyright_data.is_confirmed,
        "last_edited_by": str(copyright_data.last_edited_by) if copyright_data.last_edited_by else None,
        "created_at": copyright_data.created_at.isoformat(),
        "updated_at": copyright_data.updated_at.isoformat(),
    }
