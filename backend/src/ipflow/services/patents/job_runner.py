"""专利任务执行服务."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import zipfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.models import (
    CopyrightGenerationJob,
    PatentClaim,
    PatentData,
    Project,
    ProjectStatus,
)
from ipflow.services.patents.ai_generator import PatentAIGenerator
from ipflow.api.v1.patents.export import generate_patent_text


class PatentJobRunner:
    def __init__(self) -> None:
        self.ai_generator = PatentAIGenerator()

    async def run_generation_job(
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

        try:
            draft = self.ai_generator.generate(project, job.input_payload)
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
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
            return job

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
