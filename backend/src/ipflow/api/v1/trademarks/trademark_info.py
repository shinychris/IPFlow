"""商标信息 API.

提供商标基本信息的获取和更新接口。
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import TrademarkData, Project, ProjectType, TrademarkType, TrademarkStatus
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.utils.enums import enum_value

router = APIRouter()


# =============================================================================
# 请求/响应模型
# =============================================================================


class TrademarkInfoBase(BaseModel):
    """商标信息基础模型."""
    
    trademark_type: TrademarkType = Field(..., description="商标类型")
    trademark_name: Optional[str] = Field(None, max_length=200, description="商标名称/文字")
    description: Optional[str] = Field(None, description="商标描述")
    design_description: Optional[str] = Field(None, description="设计说明（图形商标使用）")
    color_claim: Optional[str] = Field(None, description="颜色说明")
    special_notes: Optional[str] = Field(None, description="特殊说明（特殊字体、非规范汉字等）")


class TrademarkInfoCreate(TrademarkInfoBase):
    """创建商标信息请求."""
    pass


class TrademarkInfoUpdate(BaseModel):
    """更新商标信息请求."""
    
    trademark_type: Optional[TrademarkType] = None
    trademark_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    design_description: Optional[str] = None
    color_claim: Optional[str] = None
    special_notes: Optional[str] = None


class TrademarkInfoResponse(TrademarkInfoBase):
    """商标信息响应."""
    
    id: UUID
    project_id: UUID
    status: TrademarkStatus
    upload_id: Optional[UUID]
    application_number: Optional[str]
    registration_number: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# =============================================================================
# API 端点
# =============================================================================


@router.get("/trademark-info", response_model=dict)
async def get_trademark_info(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取商标信息.
    
    获取指定商标项目的详细信息。
    """
    # 验证项目存在且属于当前用户
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 查询商标信息
    result = await db.execute(
        select(TrademarkData).where(TrademarkData.project_id == project_id)
    )
    trademark_data = result.scalar_one_or_none()
    
    if not trademark_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商标信息不存在",
        )
    
    return {
        "id": str(trademark_data.id),
        "project_id": str(trademark_data.project_id),
        "trademark_type": enum_value(trademark_data.trademark_type),
        "trademark_name": trademark_data.trademark_name,
        "description": trademark_data.description,
        "design_description": trademark_data.design_description,
        "color_claim": trademark_data.color_claim,
        "special_notes": trademark_data.special_notes,
        "status": enum_value(trademark_data.status),
        "upload_id": str(trademark_data.upload_id) if trademark_data.upload_id else None,
        "application_number": trademark_data.application_number,
        "registration_number": trademark_data.registration_number,
        "source": trademark_data.source,
        "revision": trademark_data.revision,
        "is_confirmed": trademark_data.is_confirmed,
        "last_edited_by": str(trademark_data.last_edited_by) if trademark_data.last_edited_by else None,
        "created_at": trademark_data.created_at.isoformat(),
        "updated_at": trademark_data.updated_at.isoformat(),
    }


@router.put("/trademark-info", response_model=dict)
async def update_trademark_info(
    project_id: UUID,
    data: TrademarkInfoBase,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新商标信息.
    
    创建或更新商标项目的详细信息。
    """
    from datetime import datetime
    
    # 验证项目存在且属于当前用户
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 查询是否已存在商标信息
    result = await db.execute(
        select(TrademarkData).where(TrademarkData.project_id == project_id)
    )
    trademark_data = result.scalar_one_or_none()
    
    if trademark_data:
        # 更新现有记录
        trademark_data.trademark_type = data.trademark_type
        trademark_data.trademark_name = data.trademark_name
        trademark_data.description = data.description
        trademark_data.design_description = data.design_description
        trademark_data.color_claim = data.color_claim
        trademark_data.special_notes = data.special_notes
        trademark_data.source = "human"
        trademark_data.revision += 1
        trademark_data.is_confirmed = False
        trademark_data.last_edited_by = current_user.id
        trademark_data.updated_at = datetime.utcnow()
    else:
        # 创建新记录
        trademark_data = TrademarkData(
            project_id=project_id,
            trademark_type=data.trademark_type,
            trademark_name=data.trademark_name,
            description=data.description,
            design_description=data.design_description,
            color_claim=data.color_claim,
            special_notes=data.special_notes,
            source="human",
            revision=1,
            is_confirmed=False,
            last_edited_by=current_user.id,
        )
        db.add(trademark_data)
    
    await db.commit()
    await db.refresh(trademark_data)
    
    # 更新项目
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "id": str(trademark_data.id),
        "project_id": str(trademark_data.project_id),
        "trademark_type": enum_value(trademark_data.trademark_type),
        "trademark_name": trademark_data.trademark_name,
        "description": trademark_data.description,
        "design_description": trademark_data.design_description,
        "color_claim": trademark_data.color_claim,
        "special_notes": trademark_data.special_notes,
        "status": enum_value(trademark_data.status),
        "upload_id": str(trademark_data.upload_id) if trademark_data.upload_id else None,
        "application_number": trademark_data.application_number,
        "registration_number": trademark_data.registration_number,
        "source": trademark_data.source,
        "revision": trademark_data.revision,
        "is_confirmed": trademark_data.is_confirmed,
        "last_edited_by": str(trademark_data.last_edited_by) if trademark_data.last_edited_by else None,
        "created_at": trademark_data.created_at.isoformat(),
        "updated_at": trademark_data.updated_at.isoformat(),
    }


@router.get("/trademark-info/status", response_model=dict)
async def get_trademark_status(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取商标状态."""
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 查询商标信息
    result = await db.execute(
        select(TrademarkData).where(TrademarkData.project_id == project_id)
    )
    trademark_data = result.scalar_one_or_none()
    
    if not trademark_data:
        return {
            "has_data": False,
            "status": None,
        }
    
    return {
        "has_data": True,
        "status": enum_value(trademark_data.status),
        "application_number": trademark_data.application_number,
        "registration_number": trademark_data.registration_number,
        "trademark_type": enum_value(trademark_data.trademark_type),
    }


@router.put("/trademark-info/upload", response_model=dict)
async def update_trademark_upload(
    project_id: UUID,
    upload_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新商标图样上传文件ID."""
    from datetime import datetime
    
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取商标数据
    result = await db.execute(
        select(TrademarkData).where(TrademarkData.project_id == project_id)
    )
    trademark_data = result.scalar_one_or_none()
    
    if not trademark_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商标信息不存在",
        )
    
    # 更新上传文件ID
    trademark_data.upload_id = upload_id
    trademark_data.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(trademark_data)
    
    return {
        "id": str(trademark_data.id),
        "upload_id": str(trademark_data.upload_id) if trademark_data.upload_id else None,
        "updated_at": trademark_data.updated_at.isoformat(),
    }
