"""商标生成后台任务（独立 DB 会话）."""

from __future__ import annotations

from uuid import UUID

from ipflow.db import session as db_session_module
from ipflow.models import CopyrightGenerationJob, Project
from ipflow.services.trademarks.job_runner import TrademarkJobRunner


async def run_trademark_generation_background(job_id: UUID, project_id: UUID) -> None:
    factory = db_session_module.AsyncSessionLocal
    async with factory() as db:
        job = await db.get(CopyrightGenerationJob, job_id)
        project = await db.get(Project, project_id)
        if not job or not project:
            return
        runner = TrademarkJobRunner()
        await runner.run_generation_job(db, job=job, project=project)
