"""专利任务执行服务."""

from __future__ import annotations

import zipfile
from datetime import datetime
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.api.v1.patents.export import generate_patent_text
from ipflow.config import get_settings
from ipflow.models import (
    CopyrightGenerationJob,
    PatentClaim,
    PatentData,
    Project,
    ProjectStatus,
)
from ipflow.schemas.generation_repo import parse_repo_input_from_payload
from ipflow.services.copyright.source_fetcher import (
    SourceFetchError,
    cleanup_job_source_directory,
)
from ipflow.services.generation.code_root import fetch_code_root_for_job
from ipflow.services.generation.provider_invoke import invoke_material_draft_provider
from ipflow.services.patents.draft_providers import (
    TemplatePatentDraftProvider,
    get_patent_draft_provider,
)


class PatentJobRunner:
    def __init__(self) -> None:
        pass

    async def run_generation_job(  # noqa: C901
        self,
        db: AsyncSession,
        *,
        job: CopyrightGenerationJob,
        project: Project,
    ) -> CopyrightGenerationJob:
        job.status = "running"
        job.progress = 10
        job.current_step = "生成专利草稿"
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        await db.commit()

        settings = get_settings()
        provider = get_patent_draft_provider(settings)
        should_cleanup_source = False
        code_root = None

        try:
            active = parse_repo_input_from_payload(job.input_payload)
            if active and active.effective_source_url():
                job.progress = 15
                job.current_step = "拉取源码"
                job.updated_at = datetime.utcnow()
                await db.commit()

            code_root, should_cleanup_source = await fetch_code_root_for_job(
                job.id,
                job.input_payload,
                settings=settings,
            )

            job.progress = 25
            job.current_step = "生成专利草稿"
            job.updated_at = datetime.utcnow()
            await db.commit()

            draft = await invoke_material_draft_provider(
                settings,
                backend_setting="PATENT_DRAFT_BACKEND",
                fallback_setting="PATENT_DRAFT_FALLBACK_TO_TEMPLATE",
                provider=provider,
                template_factory=TemplatePatentDraftProvider,
                project=project,
                payload=job.input_payload or {},
                code_root=code_root,
            )
            result = await db.execute(select(PatentData).where(PatentData.project_id == project.id))
            patent_data = result.scalar_one_or_none()
            if not patent_data:
                patent_data = PatentData(
                    project_id=project.id,
                    patent_type=draft.patent_info["patent_type"],
                    title=draft.patent_info["title"],
                    technical_field=draft.patent_info["technical_field"],
                    background_art=draft.patent_info["background_art"],
                    abstract=draft.patent_info["abstract"],
                    abstract_figure_number=draft.patent_info["abstract_figure_number"],
                    source="ai",
                    revision=1,
                    is_confirmed=False,
                    invention_content=draft.description["invention_content"],
                    implementation=draft.description["implementation"],
                )
                db.add(patent_data)
                await db.flush()
            else:
                patent_data.patent_type = draft.patent_info["patent_type"]
                patent_data.title = draft.patent_info["title"]
                patent_data.technical_field = draft.patent_info["technical_field"]
                patent_data.background_art = draft.patent_info["background_art"]
                patent_data.abstract = draft.patent_info["abstract"]
                patent_data.invention_content = draft.description["invention_content"]
                patent_data.implementation = draft.description["implementation"]
                patent_data.source = "mixed" if patent_data.source == "human" else "ai"
                patent_data.revision += 1
                patent_data.is_confirmed = False
                patent_data.updated_at = datetime.utcnow()

            result = await db.execute(
                select(PatentClaim).where(PatentClaim.patent_data_id == patent_data.id)
            )
            existing_claims = result.scalars().all()
            for claim in existing_claims:
                await db.delete(claim)
            await db.flush()

            for draft_claim in draft.claims:
                db.add(
                    PatentClaim(
                        patent_data_id=patent_data.id,
                        claim_number=draft_claim["claim_number"],
                        claim_type=draft_claim["claim_type"],
                        parent_claim_number=draft_claim["parent_claim_number"],
                        content=draft_claim["content"],
                    )
                )
            patent_data.claims_count = len(draft.claims)

            project.flow_status = "draft_ready"
            project.current_step = max(project.current_step, 2)
            project.updated_at = datetime.utcnow()

            job.status = "succeeded"
            job.progress = 100
            job.current_step = "已完成"
            job.result_payload = {
                "patent_info_generated": True,
                "claims_generated": len(draft.claims),
            }
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
            return job
        except SourceFetchError as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            project.flow_status = "draft_pending"
            project.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
            return job
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            project.flow_status = "draft_pending"
            project.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
            return job
        finally:
            if should_cleanup_source:
                cleanup_job_source_directory(job.id, settings)

    async def run_export_job(
        self,
        db: AsyncSession,
        *,
        job: CopyrightGenerationJob,
        project: Project,
    ) -> CopyrightGenerationJob:
        job.status = "running"
        job.progress = 20
        job.current_step = "生成专利导出包"
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        await db.commit()

        try:
            result = await db.execute(select(PatentData).where(PatentData.project_id == project.id))
            patent_data = result.scalar_one_or_none()
            if not patent_data:
                raise ValueError("请先填写专利信息")

            result = await db.execute(
                select(PatentClaim)
                .where(PatentClaim.patent_data_id == patent_data.id)
                .order_by(PatentClaim.claim_number)
            )
            claims = result.scalars().all()
            if not claims:
                raise ValueError("请至少填写一项权利要求")

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                text = generate_patent_text(patent_data, claims)
                zf.writestr(f"01_说明书_{patent_data.title}.txt", text.encode("utf-8"))
                claims_text = "权利要求书\n\n" + "\n\n".join(
                    f"{c.claim_number}. {c.content}" for c in claims
                )
                zf.writestr(f"02_权利要求书_{patent_data.title}.txt", claims_text.encode("utf-8"))
            zip_buffer.seek(0)
            content = zip_buffer.getvalue()

            project.status = ProjectStatus.PENDING_SUBMIT
            project.flow_status = "export_ready"
            project.current_step = 5
            project.updated_at = datetime.utcnow()

            job.status = "succeeded"
            job.progress = 100
            job.current_step = "已完成"
            job.result_payload = {
                "file_name": f"专利申请包_{patent_data.title}_{datetime.now().strftime('%Y%m%d')}.zip",
                "file_size": len(content),
                "download_url": f"/api/v1/patents/export-jobs/{job.id}/download",
                "content_hex": content.hex(),
            }
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
            return job
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
            return job
