"""权利要求书 API.

提供专利权利要求书的获取、创建、更新和删除接口。
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import PatentClaim, PatentData, Project, ProjectType
from ipflow.models.user import User
from ipflow.api.deps import require_active_user

router = APIRouter()


# =============================================================================
# 请求/响应模型
# =============================================================================


class PatentClaimBase(BaseModel):
    """权利要求基础模型."""
    
    claim_number: int = Field(..., ge=1, description="权利要求编号")
    claim_type: str = Field(..., description="权利要求类型: independent/dependent")
    parent_claim_number: Optional[int] = Field(None, ge=1, description="引用的权利要求编号（从属权利要求使用）")
    content: str = Field(..., min_length=1, description="权利要求内容")


class PatentClaimCreate(PatentClaimBase):
    """创建权利要求请求."""
    pass


class PatentClaimUpdate(BaseModel):
    """更新权利要求请求."""
    
    claim_type: Optional[str] = None
    parent_claim_number: Optional[int] = Field(None, ge=1)
    content: Optional[str] = None


class PatentClaimResponse(PatentClaimBase):
    """权利要求响应."""
    
    id: UUID
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# =============================================================================
# API 端点
# =============================================================================


@router.get("/claims", response_model=dict)
async def list_claims(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取权利要求列表.
    
    获取指定专利项目的所有权利要求。
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
        return {"claims": [], "total": 0}
    
    # 获取权利要求列表
    result = await db.execute(
        select(PatentClaim)
        .where(PatentClaim.patent_data_id == patent_data.id)
        .order_by(PatentClaim.claim_number)
    )
    claims = result.scalars().all()
    
    return {
        "claims": [
            {
                "id": str(claim.id),
                "claim_number": claim.claim_number,
                "claim_type": claim.claim_type,
                "parent_claim_number": claim.parent_claim_number,
                "content": claim.content,
                "created_at": claim.created_at.isoformat(),
                "updated_at": claim.updated_at.isoformat(),
            }
            for claim in claims
        ],
        "total": len(claims),
    }


@router.post("/claims", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_claim(
    project_id: UUID,
    data: PatentClaimCreate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """创建权利要求.
    
    为指定专利项目创建新的权利要求。
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
    
    # 获取或创建专利数据
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    if not patent_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建专利信息",
        )
    
    # 检查权利要求编号是否已存在
    result = await db.execute(
        select(PatentClaim).where(
            and_(
                PatentClaim.patent_data_id == patent_data.id,
                PatentClaim.claim_number == data.claim_number,
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"权利要求 {data.claim_number} 已存在",
        )
    
    # 验证从属权利要求
    if data.claim_type == "dependent":
        if not data.parent_claim_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="从属权利要求必须引用其他权利要求",
            )
        if data.parent_claim_number >= data.claim_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="从属权利要求只能引用编号更小的权利要求",
            )
    
    # 创建权利要求
    claim = PatentClaim(
        patent_data_id=patent_data.id,
        claim_number=data.claim_number,
        claim_type=data.claim_type,
        parent_claim_number=data.parent_claim_number,
        content=data.content,
    )
    db.add(claim)
    
    # 更新专利数据的权利要求数量
    patent_data.claims_count += 1
    patent_data.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(claim)
    
    return {
        "id": str(claim.id),
        "claim_number": claim.claim_number,
        "claim_type": claim.claim_type,
        "parent_claim_number": claim.parent_claim_number,
        "content": claim.content,
        "created_at": claim.created_at.isoformat(),
        "updated_at": claim.updated_at.isoformat(),
    }


@router.put("/claims/{claim_id}", response_model=dict)
async def update_claim(
    project_id: UUID,
    claim_id: UUID,
    data: PatentClaimUpdate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新权利要求."""
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
    
    # 获取权利要求
    result = await db.execute(
        select(PatentClaim).where(PatentClaim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权利要求不存在",
        )
    
    # 验证权利要求属于当前专利
    result = await db.execute(
        select(PatentData).where(
            and_(
                PatentData.id == claim.patent_data_id,
                PatentData.project_id == project_id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此权利要求",
        )
    
    # 更新字段
    if data.claim_type is not None:
        claim.claim_type = data.claim_type
    if data.parent_claim_number is not None:
        claim.parent_claim_number = data.parent_claim_number
    if data.content is not None:
        claim.content = data.content
    
    claim.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(claim)
    
    return {
        "id": str(claim.id),
        "claim_number": claim.claim_number,
        "claim_type": claim.claim_type,
        "parent_claim_number": claim.parent_claim_number,
        "content": claim.content,
        "created_at": claim.created_at.isoformat(),
        "updated_at": claim.updated_at.isoformat(),
    }


@router.delete("/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    project_id: UUID,
    claim_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除权利要求."""
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
    
    # 获取权利要求
    result = await db.execute(
        select(PatentClaim).where(PatentClaim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权利要求不存在",
        )
    
    # 验证权利要求属于当前专利
    result = await db.execute(
        select(PatentData).where(
            and_(
                PatentData.id == claim.patent_data_id,
                PatentData.project_id == project_id,
            )
        )
    )
    patent_data = result.scalar_one_or_none()
    
    if not patent_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此权利要求",
        )
    
    # 删除权利要求
    await db.delete(claim)
    
    # 更新专利数据的权利要求数量
    patent_data.claims_count = max(0, patent_data.claims_count - 1)
    patent_data.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return None
