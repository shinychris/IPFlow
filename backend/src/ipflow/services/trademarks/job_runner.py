"""商标任务执行服务."""

from __future__ import annotations

import zipfile
from datetime import datetime
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.api.v1.trademarks.export import generate_trademark_text
from ipflow.config import get_settings
from ipflow.models import (
    CopyrightGenerationJob,
    NiceClassification,
    Project,
    ProjectStatus,
    TrademarkData,
    TrademarkNiceClass,
)
from ipflow.schemas.generation_repo import parse_repo_input_from_payload
from ipflow.services.copyright.source_fetcher import (
    SourceFetchError,
    cleanup_job_source_directory,
)
from ipflow.services.generation.code_root import fetch_code_root_for_job
from ipflow.services.generation.provider_invoke import invoke_material_draft_provider
from ipflow.services.trademarks.draft_providers import (
    TemplateTrademarkDraftProvider,
    get_trademark_draft_provider,
)


class TrademarkJobRunner:
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
        job.current_step = "生成商标草稿"
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        await db.commit()

        settings = get_settings()
        provider = get_trademark_draft_provider(settings)
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
            job.current_step = "生成商标草稿"
            job.updated_at = datetime.utcnow()
            await db.commit()

            draft = await invoke_material_draft_provider(
                settings,
                backend_setting="TRADEMARK_DRAFT_BACKEND",
                fallback_setting="TRADEMARK_DRAFT_FALLBACK_TO_TEMPLATE",
                provider=provider,
                template_factory=TemplateTrademarkDraftProvider,
                project=project,
                payload=job.input_payload or {},
                code_root=code_root,
            )
            result = await db.execute(select(TrademarkData).where(TrademarkData.project_id == project.id))
            trademark_data = result.scalar_one_or_none()
            if not trademark_data:
                trademark_data = TrademarkData(
                    project_id=project.id,
                    trademark_type=draft.trademark_info["trademark_type"],
                    trademark_name=draft.trademark_info["trademark_name"],
                    description=draft.trademark_info["description"],
                    design_description=draft.trademark_info["design_description"],
                    color_claim=draft.trademark_info["color_claim"],
                    special_notes=draft.trademark_info["special_notes"],
                    source="ai",
                    revision=1,
                    is_confirmed=False,
                )
                db.add(trademark_data)
                await db.flush()
            else:
                trademark_data.trademark_type = draft.trademark_info["trademark_type"]
                trademark_data.trademark_name = draft.trademark_info["trademark_name"]
                trademark_data.description = draft.trademark_info["description"]
                trademark_data.design_description = draft.trademark_info["design_description"]
                trademark_data.color_claim = draft.trademark_info["color_claim"]
                trademark_data.special_notes = draft.trademark_info["special_notes"]
                trademark_data.source = "mixed" if trademark_data.source == "human" else "ai"
                trademark_data.revision += 1
                trademark_data.is_confirmed = False
                trademark_data.updated_at = datetime.utcnow()

            result = await db.execute(
                select(TrademarkNiceClass).where(TrademarkNiceClass.trademark_data_id == trademark_data.id)
            )
            for item in result.scalars().all():
                await db.delete(item)
            await db.flush()

            for rec in draft.nice_classes:
                result = await db.execute(
                    select(NiceClassification).where(
                        NiceClassification.class_number == rec["class_number"]
                    )
                )
                nice = result.scalar_one_or_none()
                if nice:
                    db.add(
                        TrademarkNiceClass(
                            trademark_data_id=trademark_data.id,
                            nice_class_id=nice.id,
                            goods_services=rec["goods_services"],
                        )
                    )

            project.flow_status = "draft_ready"
            project.current_step = max(project.current_step, 2)
            project.updated_at = datetime.utcnow()

            job.status = "succeeded"
            job.progress = 100
            job.current_step = "已完成"
            job.result_payload = {"trademark_info_generated": True}
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
        job.current_step = "生成商标导出包"
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        await db.commit()

        try:
            result = await db.execute(select(TrademarkData).where(TrademarkData.project_id == project.id))
            trademark_data = result.scalar_one_or_none()
            if not trademark_data:
                raise ValueError("请先填写商标信息")

            result = await db.execute(
                select(TrademarkNiceClass, NiceClassification)
                .join(NiceClassification, TrademarkNiceClass.nice_class_id == NiceClassification.id)
                .where(TrademarkNiceClass.trademark_data_id == trademark_data.id)
            )
            rows = result.all()
            if not rows:
                raise ValueError("请至少选择一个尼斯分类")

            classes = [
                {
                    "class_number": row.NiceClassification.class_number,
                    "class_name": row.NiceClassification.class_name,
                    "goods_services": row.TrademarkNiceClass.goods_services,
                }
                for row in rows
            ]

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                text = generate_trademark_text(trademark_data, classes)
                tname = trademark_data.trademark_name or "未命名商标"
                zf.writestr(f"01_商标注册申请书_{tname}.txt", text.encode("utf-8"))
            zip_buffer.seek(0)
            content = zip_buffer.getvalue()

            project.status = ProjectStatus.PENDING_SUBMIT
            project.flow_status = "export_ready"
            project.current_step = 5
            project.updated_at = datetime.utcnow()

            filename = f"商标申请包_{trademark_data.trademark_name or '未命名'}_{datetime.now().strftime('%Y%m%d')}.zip"
            job.status = "succeeded"
            job.progress = 100
            job.current_step = "已完成"
            job.result_payload = {
                "file_name": filename,
                "file_size": len(content),
                "download_url": f"/api/v1/trademarks/export-jobs/{job.id}/download",
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
