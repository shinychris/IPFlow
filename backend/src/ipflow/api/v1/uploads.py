"""文件上传 API 路由.

提供文件上传、下载、删除等功能。
"""

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter, 
    Depends, 
    File, 
    Form, 
    HTTPException, 
    UploadFile, 
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import FileUpload, Project, ProjectStatus
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.services.storage_service import get_storage_service, StorageService

router = APIRouter(prefix="/uploads", tags=["文件上传"])

# 合法文件分类白名单（与 Form 参数描述一致），防止通过 folder 拼接造成本地存储路径穿越
ALLOWED_FILE_CATEGORIES: set[str] = {"code", "proof", "manual", "drawing"}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    project_id: Optional[UUID] = Form(None, description="关联项目ID"),
    file_category: str = Form("code", description="文件分类: code, proof, manual, drawing"),
    file_type: Optional[str] = Form(None, description="文件类型: identity, contract, trademark_image 等"),
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    """上传文件.
    
    上传文件到对象存储并记录元数据。
    """
    # 白名单校验 file_category，防止通过 folder 拼接造成本地存储路径穿越
    if file_category not in ALLOWED_FILE_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"非法的文件分类: {file_category}（合法值: code, proof, manual, drawing）",
        )
    # 验证项目存在且属于当前用户
    if project_id:
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
    
    # 读取文件内容
    content = await file.read()

    # 上传安全校验：扩展名 + MIME + 魔数 + 大小
    from ipflow.services.upload_security import validate_upload

    validation = validate_upload(
        filename=file.filename,
        content_type=file.content_type,
        file_size=len(content),
        content_head=content[:16],  # 取前 16 字节做魔数嗅探
    )
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation.error,
        )

    # 上传到存储
    upload_result = storage.upload_file(
        file_data=io.BytesIO(content),
        original_filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        folder=f"{file_category}s",
    )
    
    # 创建数据库记录
    file_upload = FileUpload(
        project_id=project_id,
        uploaded_by=current_user.id,
        original_name=file.filename,
        storage_name=upload_result["storage_name"],
        storage_path=upload_result["storage_path"],
        file_size=upload_result["file_size"],
        mime_type=file.content_type or "application/octet-stream",
        checksum=upload_result["checksum"],
        file_category=file_category,
        file_type=file_type,
        processing_status="pending",
    )
    
    db.add(file_upload)
    await db.commit()
    await db.refresh(file_upload)
    
    return {
        "id": str(file_upload.id),
        "original_name": file_upload.original_name,
        "file_size": file_upload.file_size,
        "mime_type": file_upload.mime_type,
        "file_category": file_upload.file_category,
        "processing_status": file_upload.processing_status,
        "created_at": file_upload.created_at.isoformat(),
    }


@router.get("/{file_id}")
async def get_file_info(
    file_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取文件信息."""
    result = await db.execute(
        select(FileUpload).where(FileUpload.id == file_id)
    )
    file_upload = result.scalar_one_or_none()
    
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )
    
    # 验证权限（项目所有者或上传者）
    if file_upload.uploaded_by != current_user.id:
        # 检查是否是项目所有者
        if file_upload.project_id:
            result = await db.execute(
                select(Project).where(
                    Project.id == file_upload.project_id,
                    Project.owner_id == current_user.id,
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此文件",
                )
    
    return {
        "id": str(file_upload.id),
        "project_id": str(file_upload.project_id) if file_upload.project_id else None,
        "original_name": file_upload.original_name,
        "storage_name": file_upload.storage_name,
        "file_size": file_upload.file_size,
        "mime_type": file_upload.mime_type,
        "checksum": file_upload.checksum,
        "file_category": file_upload.file_category,
        "file_type": file_upload.file_type,
        "processing_status": file_upload.processing_status,
        "processing_result": file_upload.processing_result,
        "created_at": file_upload.created_at.isoformat(),
    }


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> None:
    """删除文件."""
    result = await db.execute(
        select(FileUpload).where(FileUpload.id == file_id)
    )
    file_upload = result.scalar_one_or_none()
    
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )
    
    # 验证权限
    if file_upload.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此文件",
        )
    
    # 删除存储中的文件
    try:
        storage.delete_file(file_upload.storage_path)
    except Exception:
        # 记录错误但继续删除数据库记录
        pass
    
    # 删除数据库记录
    await db.delete(file_upload)
    await db.commit()


import io  # 放在文件末尾避免循环导入
