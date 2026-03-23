"""操作说明书 API.

提供操作说明书的创建、更新、查询、删除等功能。
"""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import CopyrightManual, CopyrightData, Project, ManualTemplateType
from ipflow.models.user import User
from ipflow.api.deps import require_active_user

router = APIRouter()


# =============================================================================
# 请求/响应模型
# =============================================================================


class ManualBase(BaseModel):
    """说明书基础模型."""
    
    template_type: ManualTemplateType = ManualTemplateType.WEB
    title: str = Field(default="软件操作说明书", max_length=100)
    content_html: Optional[str] = None
    content_json: Optional[dict] = None


class ManualCreate(ManualBase):
    """创建说明书请求."""
    pass


class ManualUpdate(BaseModel):
    """更新说明书请求."""
    
    template_type: Optional[ManualTemplateType] = None
    title: Optional[str] = Field(None, max_length=100)
    content_html: Optional[str] = None
    content_json: Optional[dict] = None
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    has_toc: Optional[bool] = None
    has_chapters: Optional[bool] = None


class ManualResponse(ManualBase):
    """说明书响应."""
    
    id: UUID
    copyright_data_id: UUID
    word_count: Optional[int]
    page_count: Optional[int]
    screenshot_count: int
    has_toc: bool
    has_chapters: bool
    created_at: str
    updated_at: str


# =============================================================================
# API 端点
# =============================================================================


@router.get("/manuals", response_model=dict)
async def list_manuals(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取说明书列表."""
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
    
    # 获取软著数据
    result = await db.execute(
        select(CopyrightData).where(CopyrightData.project_id == project_id)
    )
    copyright_data = result.scalar_one_or_none()
    
    if not copyright_data:
        return {"items": [], "total": 0}
    
    # 获取说明书列表
    result = await db.execute(
        select(CopyrightManual).where(
            CopyrightManual.copyright_data_id == copyright_data.id
        )
    )
    manuals = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(m.id),
                "template_type": m.template_type,
                "title": m.title,
                "source": m.source,
                "revision": m.revision,
                "is_confirmed": m.is_confirmed,
                "word_count": m.word_count,
                "page_count": m.page_count,
                "screenshot_count": m.screenshot_count,
                "has_toc": m.has_toc,
                "has_chapters": m.has_chapters,
                "created_at": m.created_at.isoformat(),
            }
            for m in manuals
        ],
        "total": len(manuals),
    }


@router.post("/manuals", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_manual(
    project_id: UUID,
    data: ManualCreate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """创建操作说明书."""
    from datetime import datetime
    
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
    
    # 获取软著数据
    result = await db.execute(
        select(CopyrightData).where(CopyrightData.project_id == project_id)
    )
    copyright_data = result.scalar_one_or_none()
    
    if not copyright_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请先填写软件信息",
        )
    
    # 计算字数和页数
    word_count = 0
    page_count = 0
    if data.content_html:
        # 简单计算：移除 HTML 标签后统计
        import re
        text = re.sub(r'<[^>]+>', '', data.content_html)
        word_count = len(text)
        # 假设每页 800 字
        page_count = max(1, word_count // 800)
    
    manual = CopyrightManual(
        id=uuid4(),
        copyright_data_id=copyright_data.id,
        template_type=data.template_type.value,
        title=data.title,
        content_html=data.content_html,
        content_json=data.content_json,
        word_count=word_count,
        page_count=page_count,
        screenshot_count=0,
        has_toc=False,
        has_chapters=False,
        source="human",
        revision=1,
        is_confirmed=False,
        last_edited_by=current_user.id,
    )
    
    db.add(manual)
    await db.commit()
    await db.refresh(manual)
    
    return {
        "id": str(manual.id),
        "template_type": manual.template_type,
        "title": manual.title,
        "source": manual.source,
        "revision": manual.revision,
        "is_confirmed": manual.is_confirmed,
        "word_count": manual.word_count,
        "page_count": manual.page_count,
        "screenshot_count": manual.screenshot_count,
        "has_toc": manual.has_toc,
        "has_chapters": manual.has_chapters,
        "created_at": manual.created_at.isoformat(),
    }


@router.get("/manuals/{manual_id}", response_model=dict)
async def get_manual(
    project_id: UUID,
    manual_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取说明书详情."""
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
    
    # 获取说明书
    result = await db.execute(
        select(CopyrightManual).where(CopyrightManual.id == manual_id)
    )
    manual = result.scalar_one_or_none()
    
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="说明书不存在",
        )
    
    return {
        "id": str(manual.id),
        "copyright_data_id": str(manual.copyright_data_id),
        "template_type": manual.template_type,
        "title": manual.title,
        "content_html": manual.content_html,
        "content_json": manual.content_json,
        "source": manual.source,
        "revision": manual.revision,
        "is_confirmed": manual.is_confirmed,
        "last_edited_by": str(manual.last_edited_by) if manual.last_edited_by else None,
        "word_count": manual.word_count,
        "page_count": manual.page_count,
        "screenshot_count": manual.screenshot_count,
        "has_toc": manual.has_toc,
        "has_chapters": manual.has_chapters,
        "created_at": manual.created_at.isoformat(),
        "updated_at": manual.updated_at.isoformat(),
    }


@router.put("/manuals/{manual_id}", response_model=dict)
async def update_manual(
    project_id: UUID,
    manual_id: UUID,
    data: ManualUpdate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新说明书."""
    from datetime import datetime
    
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
    
    # 获取说明书
    result = await db.execute(
        select(CopyrightManual).where(CopyrightManual.id == manual_id)
    )
    manual = result.scalar_one_or_none()
    
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="说明书不存在",
        )
    
    # 更新字段
    if data.template_type is not None:
        manual.template_type = data.template_type.value
    if data.title is not None:
        manual.title = data.title
    if data.content_html is not None:
        manual.content_html = data.content_html
        # 重新计算字数和页数
        import re
        text = re.sub(r'<[^>]+>', '', data.content_html)
        manual.word_count = len(text)
        manual.page_count = max(1, manual.word_count // 800)
    if data.content_json is not None:
        manual.content_json = data.content_json
    if data.has_toc is not None:
        manual.has_toc = data.has_toc
    if data.has_chapters is not None:
        manual.has_chapters = data.has_chapters
    manual.source = "human"
    manual.revision += 1
    manual.is_confirmed = False
    manual.last_edited_by = current_user.id
    
    manual.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(manual)
    
    return {
        "id": str(manual.id),
        "template_type": manual.template_type,
        "title": manual.title,
        "source": manual.source,
        "revision": manual.revision,
        "is_confirmed": manual.is_confirmed,
        "word_count": manual.word_count,
        "page_count": manual.page_count,
        "screenshot_count": manual.screenshot_count,
        "has_toc": manual.has_toc,
        "has_chapters": manual.has_chapters,
        "created_at": manual.created_at.isoformat(),
        "updated_at": manual.updated_at.isoformat(),
    }


@router.delete("/manuals/{manual_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manual(
    project_id: UUID,
    manual_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除说明书."""
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
    
    # 获取说明书
    result = await db.execute(
        select(CopyrightManual).where(CopyrightManual.id == manual_id)
    )
    manual = result.scalar_one_or_none()
    
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="说明书不存在",
        )
    
    await db.delete(manual)
    await db.commit()


@router.get("/manuals/{manual_id}/stats", response_model=dict)
async def get_manual_stats(
    project_id: UUID,
    manual_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取说明书统计信息."""
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
    
    # 获取说明书
    result = await db.execute(
        select(CopyrightManual).where(CopyrightManual.id == manual_id)
    )
    manual = result.scalar_one_or_none()
    
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="说明书不存在",
        )
    
    # 合规检查提示
    warnings = []
    if manual.page_count < 15:
        warnings.append("说明书不足15页，建议补充更多内容")
    if not manual.has_toc:
        warnings.append("建议添加目录")
    if not manual.has_chapters:
        warnings.append("建议添加规范章节")
    
    return {
        "word_count": manual.word_count,
        "page_count": manual.page_count,
        "screenshot_count": manual.screenshot_count,
        "has_toc": manual.has_toc,
        "has_chapters": manual.has_chapters,
        "compliance": {
            "min_pages_met": manual.page_count >= 15,
            "warnings": warnings,
        },
    }
