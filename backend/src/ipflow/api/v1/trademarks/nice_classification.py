"""尼斯分类 API.

提供尼斯分类的查询和商标分类关联接口。
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import (
    NiceClassification, TrademarkNiceClass, TrademarkData, 
    Project, ProjectType
)
from ipflow.models.user import User
from ipflow.api.deps import require_active_user

router = APIRouter()


# =============================================================================
# 请求/响应模型
# =============================================================================


class NiceClassBase(BaseModel):
    """尼斯分类基础模型."""
    
    class_number: int = Field(..., ge=1, le=45, description="类别号 1-45")
    goods_services: List[str] = Field(default_factory=list, description="具体商品/服务项目")


class NiceClassCreate(NiceClassBase):
    """创建尼斯分类关联请求."""
    pass


class NiceClassUpdate(BaseModel):
    """更新尼斯分类关联请求."""
    
    goods_services: List[str] = Field(default_factory=list, description="具体商品/服务项目")


class NiceClassInfo(BaseModel):
    """尼斯分类信息响应."""
    
    id: UUID
    class_number: int
    class_name: str
    description: Optional[str]


# =============================================================================
# API 端点 - 尼斯分类查询（全局）
# =============================================================================


@router.get("/nice-classes", response_model=dict)
async def list_nice_classes(
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    class_number: Optional[int] = Query(None, ge=1, le=45, description="按类别号筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> dict:
    """获取尼斯分类列表.
    
    查询所有尼斯分类或按条件筛选。
    """
    query = select(NiceClassification).where(NiceClassification.is_active == True)
    
    if class_number:
        query = query.where(NiceClassification.class_number == class_number)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (NiceClassification.class_name.ilike(search_term)) |
            (NiceClassification.class_name_en.ilike(search_term)) |
            (NiceClassification.description.ilike(search_term))
        )
    
    # 获取总数
    count_result = await db.execute(
        select(select(NiceClassification).where(NiceClassification.is_active == True).subquery())
    )
    total = len(count_result.all())
    
    # 分页
    query = query.order_by(NiceClassification.class_number)
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    classes = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(c.id),
                "class_number": c.class_number,
                "class_name": c.class_name,
                "class_name_en": c.class_name_en,
                "description": c.description,
            }
            for c in classes
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/nice-classes/by-id/{class_id}", response_model=dict)
async def get_nice_class(
    class_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取单个尼斯分类详情."""
    result = await db.execute(
        select(NiceClassification).where(NiceClassification.id == class_id)
    )
    nice_class = result.scalar_one_or_none()
    
    if not nice_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尼斯分类不存在",
        )
    
    return {
        "id": str(nice_class.id),
        "class_number": nice_class.class_number,
        "class_name": nice_class.class_name,
        "class_name_en": nice_class.class_name_en,
        "description": nice_class.description,
    }


# =============================================================================
# API 端点 - 商标分类关联
# =============================================================================


@router.get("/nice-classes/selected", response_model=dict)
async def get_trademark_nice_classes(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取商标已选择的尼斯分类.
    
    获取指定商标项目已选择的所有尼斯分类。
    """
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
        return {"items": [], "total": 0}
    
    # 获取已选择的分类
    result = await db.execute(
        select(TrademarkNiceClass, NiceClassification)
        .join(NiceClassification, TrademarkNiceClass.nice_class_id == NiceClassification.id)
        .where(TrademarkNiceClass.trademark_data_id == trademark_data.id)
        .order_by(NiceClassification.class_number)
    )
    rows = result.all()
    
    return {
        "items": [
            {
                "id": str(row.TrademarkNiceClass.id),
                "class_id": str(row.NiceClassification.id),
                "class_number": row.NiceClassification.class_number,
                "class_name": row.NiceClassification.class_name,
                "goods_services": row.TrademarkNiceClass.goods_services,
            }
            for row in rows
        ],
        "total": len(rows),
    }


@router.post("/nice-classes/selected", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_nice_class_to_trademark(
    project_id: UUID,
    data: NiceClassCreate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """添加尼斯分类到商标.
    
    为指定商标项目添加尼斯分类。
    """
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建商标信息",
        )
    
    # 获取尼斯分类
    result = await db.execute(
        select(NiceClassification).where(
            NiceClassification.class_number == data.class_number
        )
    )
    nice_class = result.scalar_one_or_none()
    
    if not nice_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"尼斯分类第 {data.class_number} 类不存在",
        )
    
    # 检查是否已添加
    result = await db.execute(
        select(TrademarkNiceClass).where(
            and_(
                TrademarkNiceClass.trademark_data_id == trademark_data.id,
                TrademarkNiceClass.nice_class_id == nice_class.id,
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"第 {data.class_number} 类已添加",
        )
    
    # 创建关联
    trademark_nice_class = TrademarkNiceClass(
        trademark_data_id=trademark_data.id,
        nice_class_id=nice_class.id,
        goods_services=data.goods_services,
    )
    db.add(trademark_nice_class)
    
    await db.commit()
    await db.refresh(trademark_nice_class)
    
    return {
        "id": str(trademark_nice_class.id),
        "class_id": str(nice_class.id),
        "class_number": nice_class.class_number,
        "class_name": nice_class.class_name,
        "goods_services": trademark_nice_class.goods_services,
        "created_at": trademark_nice_class.created_at.isoformat(),
    }


@router.put("/nice-classes/selected/{association_id}", response_model=dict)
async def update_trademark_nice_class(
    project_id: UUID,
    association_id: UUID,
    data: NiceClassUpdate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新商标尼斯分类的商品/服务列表."""
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
    
    # 获取关联
    result = await db.execute(
        select(TrademarkNiceClass).where(
            and_(
                TrademarkNiceClass.id == association_id,
                TrademarkNiceClass.trademark_data_id == trademark_data.id,
            )
        )
    )
    association = result.scalar_one_or_none()
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类关联不存在",
        )
    
    # 更新
    association.goods_services = data.goods_services
    association.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(association)
    
    # 获取尼斯分类信息
    result = await db.execute(
        select(NiceClassification).where(NiceClassification.id == association.nice_class_id)
    )
    nice_class = result.scalar_one()
    
    return {
        "id": str(association.id),
        "class_id": str(nice_class.id),
        "class_number": nice_class.class_number,
        "class_name": nice_class.class_name,
        "goods_services": association.goods_services,
        "updated_at": association.updated_at.isoformat(),
    }


@router.delete("/nice-classes/selected/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_nice_class_from_trademark(
    project_id: UUID,
    association_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """从商标移除尼斯分类."""
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
    
    # 获取关联
    result = await db.execute(
        select(TrademarkNiceClass).where(
            and_(
                TrademarkNiceClass.id == association_id,
                TrademarkNiceClass.trademark_data_id == trademark_data.id,
            )
        )
    )
    association = result.scalar_one_or_none()
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类关联不存在",
        )
    
    # 删除
    await db.delete(association)
    await db.commit()
    
    return None
