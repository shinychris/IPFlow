"""专利导出任务 API."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.api.deps import require_active_user
from ipflow.core.content_disposition import build_content_disposition
from ipflow.db import get_db
from ipflow.models import CopyrightGenerationJob, Project, ProjectType
from ipflow.models.user import User
from ipflow.services.patents.job_runner import PatentJobRunner

router = APIRouter()
runner = PatentJobRunner()


@router.post("/projects/{project_id}/export-jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_export_job(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.PATENT,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    project.flow_status = "exporting"
    project.updated_at = datetime.utcnow()
    job = CopyrightGenerationJob(
        project_id=project.id,
        project_type="patent",
        job_domain="patents",
        job_type="export",
        status="queued",
        progress=0,
        current_step="等待执行",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await runner.run_export_job(db, job=job, project=project)
    return {"export_job_id": str(job.id), "status": job.status, "progress": job.progress}


@router.get("/export-jobs/{job_id}", response_model=dict)
async def get_export_job(
    job_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(CopyrightGenerationJob, Project)
        .join(Project, Project.id == CopyrightGenerationJob.project_id)
        .where(
            CopyrightGenerationJob.id == job_id,
            CopyrightGenerationJob.job_domain == "patents",
            CopyrightGenerationJob.job_type == "export",
            Project.owner_id == current_user.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导出任务不存在")
    job, _project = row
    payload = job.result_payload or {}
    return {
        "id": str(job.id),
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "error": job.error_message,
        "download_url": payload.get("download_url"),
        "file_name": payload.get("file_name"),
        "expires_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        if job.status == "succeeded"
        else None,
        "created_at": job.created_at.isoformat(),
    }


@router.get("/projects/{project_id}/export-jobs", response_model=dict)
async def list_export_jobs(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.PATENT,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    result = await db.execute(
        select(CopyrightGenerationJob)
        .where(
            CopyrightGenerationJob.project_id == project_id,
            CopyrightGenerationJob.job_domain == "patents",
            CopyrightGenerationJob.job_type == "export",
        )
        .order_by(desc(CopyrightGenerationJob.created_at))
    )
    jobs = result.scalars().all()
    return {
        "items": [{"id": str(job.id), "status": job.status, "progress": job.progress} for job in jobs],
        "total": len(jobs),
    }


@router.get("/export-jobs/{job_id}/download")
async def download_export_job(
    job_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CopyrightGenerationJob, Project)
        .join(Project, Project.id == CopyrightGenerationJob.project_id)
        .where(
            CopyrightGenerationJob.id == job_id,
            CopyrightGenerationJob.job_domain == "patents",
            CopyrightGenerationJob.job_type == "export",
            Project.owner_id == current_user.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导出任务不存在")
    job, _project = row
    if job.status != "succeeded":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导出任务尚未完成")
    payload = job.result_payload or {}
    content_hex = payload.get("content_hex")
    if not content_hex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导出文件不存在")
    data = bytes.fromhex(content_hex)
    return StreamingResponse(
        iter([data]),
        media_type="application/zip",
        headers={"Content-Disposition": build_content_disposition(payload.get("file_name", "export.zip"))},
    )
