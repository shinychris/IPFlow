"""代码包 API.

提供代码包的上传、处理、查询、删除等功能。
"""

import io
import tempfile
from typing import List, Optional
from uuid import UUID, uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import (
    CodeBundle, 
    CopyrightData, 
    FileUpload, 
    Project, 
    ProjectType,
)
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.services.copyright.code_processor import CodeProcessor
from ipflow.services.storage_service import get_storage_service, StorageService

router = APIRouter()


@router.get("/code-bundles", response_model=dict)
async def list_code_bundles(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取代码包列表."""
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
    
    # 获取代码包列表
    result = await db.execute(
        select(CodeBundle).where(
            CodeBundle.copyright_data_id == copyright_data.id
        )
    )
    bundles = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(b.id),
                "original_file_name": b.original_file_name,
                "original_file_size": b.original_file_size,
                "total_files": b.total_files,
                "total_lines": b.total_lines,
                "processed_lines": b.processed_lines,
                "has_enough_code": b.has_enough_code,
                "warnings": b.warnings,
                "language_stats": b.language_stats,
                "created_at": b.created_at.isoformat(),
            }
            for b in bundles
        ],
        "total": len(bundles),
    }


@router.post("/code-bundles", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_code_bundle(
    project_id: UUID,
    file: UploadFile = File(..., description="源代码 ZIP 文件"),
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    """上传并处理代码包.
    
    上传 ZIP 文件，自动提取代码并生成前30页+后30页。
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
    
    # 读取 ZIP 文件
    content = await file.read()
    
    # 上传原始文件到存储
    upload_result = storage.upload_file(
        file_data=io.BytesIO(content),
        original_filename=file.filename,
        content_type="application/zip",
        folder="code_bundles",
    )
    
    # 创建文件上传记录
    file_upload = FileUpload(
        project_id=project_id,
        uploaded_by=current_user.id,
        original_name=file.filename,
        storage_name=upload_result["storage_name"],
        storage_path=upload_result["storage_path"],
        file_size=upload_result["file_size"],
        mime_type="application/zip",
        checksum=upload_result["checksum"],
        file_category="code",
        file_type="source_code",
        processing_status="processing",
    )
    db.add(file_upload)
    await db.flush()  # 获取 file_upload.id
    
    # 处理代码
    try:
        processor = CodeProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = processor.process_zip_file(
                zip_file=io.BytesIO(content),
                extract_dir=Path(temp_dir) / "extract",
                software_name=copyright_data.software_full_name,
                version=copyright_data.version_number,
            )
            
            # 创建代码包记录
            code_bundle = CodeBundle(
                id=uuid4(),
                copyright_data_id=copyright_data.id,
                upload_id=file_upload.id,
                original_file_name=file.filename,
                original_file_size=len(content),
                total_files=result["total_files"],
                total_lines=result["total_lines"],
                processed_lines=result["processed_lines"],
                pages_data=[
                    {
                        "page_number": p["page_number"],
                        "content": p["content"],
                        "line_start": p["line_start"],
                        "line_end": p["line_end"],
                        "section": p["section"],
                    }
                    for p in result["pages"]
                ],
                language_stats=result["language_stats"],
                has_enough_code=result["has_enough_code"],
                warnings=result["warnings"],
            )
            db.add(code_bundle)
            
            # 更新文件处理状态
            file_upload.processing_status = "completed"
            file_upload.processing_result = {
                "total_files": result["total_files"],
                "total_lines": result["total_lines"],
                "has_enough_code": result["has_enough_code"],
            }
            
            # 更新软著数据的代码行数
            copyright_data.code_line_count = result["total_lines"]
            copyright_data.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(code_bundle)
            
            return {
                "id": str(code_bundle.id),
                "original_file_name": code_bundle.original_file_name,
                "total_files": code_bundle.total_files,
                "total_lines": code_bundle.total_lines,
                "processed_lines": code_bundle.processed_lines,
                "has_enough_code": code_bundle.has_enough_code,
                "warnings": code_bundle.warnings,
                "language_stats": code_bundle.language_stats,
                "created_at": code_bundle.created_at.isoformat(),
            }
            
    except Exception as e:
        # 处理失败
        file_upload.processing_status = "failed"
        file_upload.processing_result = {"error": str(e)}
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码处理失败: {str(e)}",
        )


@router.get("/code-bundles/{bundle_id}", response_model=dict)
async def get_code_bundle(
    project_id: UUID,
    bundle_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取代码包详情."""
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
    
    # 获取代码包
    result = await db.execute(
        select(CodeBundle).where(CodeBundle.id == bundle_id)
    )
    bundle = result.scalar_one_or_none()
    
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代码包不存在",
        )
    
    return {
        "id": str(bundle.id),
        "original_file_name": bundle.original_file_name,
        "original_file_size": bundle.original_file_size,
        "total_files": bundle.total_files,
        "total_lines": bundle.total_lines,
        "processed_lines": bundle.processed_lines,
        "pages_data": bundle.pages_data,
        "language_stats": bundle.language_stats,
        "has_enough_code": bundle.has_enough_code,
        "warnings": bundle.warnings,
        "created_at": bundle.created_at.isoformat(),
    }


@router.delete("/code-bundles/{bundle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_code_bundle(
    project_id: UUID,
    bundle_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> None:
    """删除代码包."""
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
    
    # 获取代码包
    result = await db.execute(
        select(CodeBundle).where(CodeBundle.id == bundle_id)
    )
    bundle = result.scalar_one_or_none()
    
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代码包不存在",
        )
    
    # 删除关联的文件上传记录
    if bundle.upload_id:
        result = await db.execute(
            select(FileUpload).where(FileUpload.id == bundle.upload_id)
        )
        file_upload = result.scalar_one_or_none()
        if file_upload:
            # 删除存储中的文件
            try:
                storage.delete_file(file_upload.storage_path)
            except Exception:
                pass
            # 删除数据库记录
            await db.delete(file_upload)
    
    # 删除代码包记录
    await db.delete(bundle)
    await db.commit()


@router.get("/code-bundles/{bundle_id}/preview", response_model=dict)
async def preview_code_bundle(
    project_id: UUID,
    bundle_id: UUID,
    page: int = 1,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """预览代码包（指定页）."""
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
    
    # 获取代码包
    result = await db.execute(
        select(CodeBundle).where(CodeBundle.id == bundle_id)
    )
    bundle = result.scalar_one_or_none()
    
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代码包不存在",
        )
    
    # 查找指定页
    page_data = None
    for p in bundle.pages_data:
        if p["page_number"] == page:
            page_data = p
            break
    
    if not page_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="页码不存在",
        )
    
    return {
        "page_number": page_data["page_number"],
        "content": page_data["content"],
        "line_start": page_data["line_start"],
        "line_end": page_data["line_end"],
        "section": page_data["section"],
    }
