"""商标生成任务 API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.api.deps import require_active_user
from ipflow.db import get_db
from ipflow.models import CopyrightGenerationJob, Project, ProjectType, TrademarkData
from ipflow.models.user import User
from ipflow.services.trademarks.job_runner import TrademarkJobRunner

router = APIRouter()
runner = TrademarkJobRunner()


class GenerationInputs(BaseModel):
    extra_brief: str | None = None
    history_reuse: dict | None = None
    org_knowledge: dict | None = None


class GenerationPolicy(BaseModel):
    overwrite_strategy: str = "fill_blank_only"


class StartGenerationRequest(BaseModel):
    generation_mode: str = Field(default="guided_confirm")
    inputs: GenerationInputs = Field(default_factory=GenerationInputs)
    policy: GenerationPolicy = Field(default_factory=GenerationPolicy)


@router.get("/projects/{project_id}/generation-context", response_model=dict)
async def get_generation_context(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    return {
        "project_id": str(project.id),
        "project_type": project.project_type.value,
        "base_profile": {
            "name": project.name,
            "version": project.version,
            "description": project.description,
        },
        "optional_inputs": {
            "extra_brief": project.description,
            "history_reuse": {"enabled": False, "source_project_ids": []},
            "org_knowledge": {"enabled": False, "dataset_ids": []},
        },
        "capability_flags": {
            "can_use_history": False,
            "can_use_org_knowledge": False,
            "can_use_repo": False,
        },
    }


@router.post("/projects/{project_id}/generation-jobs", status_code=status.HTTP_202_ACCEPTED)
async def start_generation_job(
    project_id: UUID,
    request: StartGenerationRequest,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    project.flow_status = "generating"
    project.updated_at = datetime.utcnow()
    job = CopyrightGenerationJob(
        project_id=project.id,
        project_type="trademark",
        job_domain="trademarks",
        job_type="ai_draft",
        status="queued",
        progress=0,
        current_step="等待执行",
        input_payload=request.model_dump(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await runner.run_generation_job(db, job=job, project=project)
    return {"job_id": str(job.id), "status": job.status, "progress": job.progress}


@router.get("/generation-jobs/{job_id}", response_model=dict)
async def get_generation_job(
    job_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(CopyrightGenerationJob, Project)
        .join(Project, Project.id == CopyrightGenerationJob.project_id)
        .where(
            CopyrightGenerationJob.id == job_id,
            CopyrightGenerationJob.job_domain == "trademarks",
            Project.owner_id == current_user.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    job, _project = row
    return {
        "id": str(job.id),
        "project_id": str(job.project_id),
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "error": job.error_message,
        "artifacts": job.result_payload,
        "created_at": job.created_at.isoformat(),
    }


@router.get("/projects/{project_id}/generation-jobs", response_model=dict)
async def list_generation_jobs(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    result = await db.execute(
        select(CopyrightGenerationJob)
        .where(
            CopyrightGenerationJob.project_id == project_id,
            CopyrightGenerationJob.job_domain == "trademarks",
            CopyrightGenerationJob.job_type != "export",
        )
        .order_by(desc(CopyrightGenerationJob.created_at))
    )
    jobs = result.scalars().all()
    return {
        "items": [{"id": str(job.id), "status": job.status, "progress": job.progress} for job in jobs],
        "total": len(jobs),
    }


@router.post("/projects/{project_id}/materials/confirm", response_model=dict)
async def confirm_materials(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    result = await db.execute(select(TrademarkData).where(TrademarkData.project_id == project_id))
    trademark_data = result.scalar_one_or_none()
    if not trademark_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先生成商标草稿")
    trademark_data.is_confirmed = True
    trademark_data.last_edited_by = current_user.id
    trademark_data.updated_at = datetime.utcnow()
    project.flow_status = "human_editing"
    project.updated_at = datetime.utcnow()
    await db.commit()
    return {"project_id": str(project_id), "flow_status": project.flow_status}
