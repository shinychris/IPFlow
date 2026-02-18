"""项目 API 路由.

提供项目管理的 CRUD 操作。
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import (
    Project, 
    ProjectType, 
    ProjectStatus, 
    SubjectType,
    ProjectResponse,
    ProjectCreate,
    ProjectUpdate,
)
from ipflow.api.deps import get_current_user, require_active_user
from ipflow.models.user import User

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    project_type: ProjectType | None = Query(None, description="项目类型筛选"),
    status: ProjectStatus | None = Query(None, description="状态筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[Project]:
    """获取项目列表.
    
    支持按项目类型和状态筛选，仅返回当前用户的项目。
    """
    query = select(Project).where(Project.owner_id == current_user.id)
    
    if project_type:
        query = query.where(Project.project_type == project_type)
    
    if status:
        query = query.where(Project.status == status)
    
    query = query.order_by(desc(Project.updated_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """创建新项目.
    
    创建一个新的软著/专利/商标项目。
    """
    project = Project(
        owner_id=current_user.id,
        name=project_in.name,
        project_type=project_in.project_type,
        subject_type=project_in.subject_type,
        version=project_in.version,
        description=project_in.description,
        development_method=project_in.development_method,
        publication_status=project_in.publication_status,
        subject_name=project_in.subject_name,
        subject_id_number=project_in.subject_id_number,
        status=ProjectStatus.DRAFT,
        current_step=1,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """获取项目详情.
    
    获取指定项目的详细信息。
    """
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


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """更新项目.
    
    部分更新项目信息。
    """
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
    
    # 只更新提供的字段
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除项目（软删除）.
    
    将项目标记为已删除，不实际删除数据。
    """
    from datetime import datetime
    
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
    
    # 软删除
    project.deleted_at = datetime.utcnow()
    await db.commit()


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_project(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """复制项目.
    
    创建项目的副本，保留原项目信息。
    """
    from uuid import uuid4
    from datetime import datetime
    
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 创建副本
    new_project = Project(
        id=uuid4(),
        owner_id=current_user.id,
        project_type=original.project_type,
        name=f"{original.name} (副本)",
        version=original.version,
        description=original.description,
        subject_type=original.subject_type,
        subject_name=original.subject_name,
        subject_id_number=original.subject_id_number,
        development_method=original.development_method,
        publication_status=original.publication_status,
        completion_date=original.completion_date,
        first_publication_date=original.first_publication_date,
        tags=original.tags,
        meta_info=original.meta_info,
        status=ProjectStatus.DRAFT,
        current_step=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    return new_project
