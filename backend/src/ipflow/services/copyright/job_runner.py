"""软著任务执行服务."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.config import get_settings
from ipflow.models import (
    CodeBundle,
    CopyrightData,
    CopyrightGenerationJob,
    CopyrightManual,
    Project,
)
from ipflow.schemas.generation_repo import parse_repo_input_from_payload
from ipflow.services.copyright.compliance_checker import ComplianceChecker
from ipflow.services.copyright.draft_providers import (
    TemplateCopyrightDraftProvider,
    get_copyright_draft_provider,
)
from ipflow.services.copyright.export_generator import ExportConfig, ExportGenerator
from ipflow.services.copyright.source_fetcher import (
    SourceFetchError,
    cleanup_job_source_directory,
)
from ipflow.services.generation.code_root import fetch_code_root_for_job
from ipflow.services.generation.provider_invoke import invoke_material_draft_provider


class CopyrightJobRunner:
    """执行软著生成与导出任务."""

    def __init__(self) -> None:
        self.export_generator = ExportGenerator()
        self.compliance_checker = ComplianceChecker()

    async def run_generation_job(  # noqa: C901
        self,
        db: AsyncSession,
        *,
        job: CopyrightGenerationJob,
        project: Project,
    ) -> CopyrightGenerationJob:
        """执行 AI 草稿生成任务."""
        job.status = "running"
        job.progress = 10
        job.current_step = "生成草稿"
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        await db.commit()

        settings = get_settings()
        provider = get_copyright_draft_provider(settings)
        code_root: Path | None = None
        should_cleanup_source = False

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
            job.current_step = "生成草稿"
            job.updated_at = datetime.utcnow()
            await db.commit()

            draft = await invoke_material_draft_provider(
                settings,
                backend_setting="COPYRIGHT_DRAFT_BACKEND",
                fallback_setting="COPYRIGHT_DRAFT_FALLBACK_TO_TEMPLATE",
                provider=provider,
                template_factory=TemplateCopyrightDraftProvider,
                project=project,
                payload=job.input_payload or {},
                code_root=code_root,
            )

            result = await db.execute(
                select(CopyrightData).where(CopyrightData.project_id == project.id)
            )
            copyright_data = result.scalar_one_or_none()

            if copyright_data:
                overwrite_strategy = (
                    (job.input_payload or {})
                    .get("policy", {})
                    .get("overwrite_strategy", "fill_blank_only")
                )
                if overwrite_strategy == "new_revision":
                    copyright_data.revision += 1
                if overwrite_strategy == "fill_blank_only":
                    self._fill_blank_software_info(copyright_data, draft.software_info)
                else:
                    self._overwrite_software_info(copyright_data, draft.software_info)
                copyright_data.source = "mixed" if copyright_data.source == "human" else "ai"
                copyright_data.is_confirmed = False
                copyright_data.updated_at = datetime.utcnow()
            else:
                copyright_data = CopyrightData(
                    project_id=project.id,
                    software_full_name=draft.software_info["software_full_name"],
                    software_short_name=draft.software_info["software_short_name"],
                    version_number=draft.software_info["version_number"],
                    development_language=draft.software_info["development_language"],
                    development_environment=draft.software_info["development_environment"],
                    runtime_environment=draft.software_info["runtime_environment"],
                    code_line_count=draft.software_info["code_line_count"],
                    functional_description=draft.software_info["functional_description"],
                    technical_features=draft.software_info["technical_features"],
                    target_domain=draft.software_info["target_domain"],
                    source="ai",
                    revision=1,
                    is_confirmed=False,
                )
                db.add(copyright_data)
                await db.flush()

            result = await db.execute(
                select(CopyrightManual)
                .where(CopyrightManual.copyright_data_id == copyright_data.id)
                .order_by(CopyrightManual.created_at.desc())
            )
            manual = result.scalars().first()
            if manual:
                manual.revision += 1
                manual.source = "mixed" if manual.source == "human" else "ai"
                manual.is_confirmed = False
                manual.title = draft.manual["title"]
                manual.content_html = draft.manual["content_html"]
                manual.updated_at = datetime.utcnow()
            else:
                manual = CopyrightManual(
                    copyright_data_id=copyright_data.id,
                    template_type=draft.manual["template_type"],
                    title=draft.manual["title"],
                    content_html=draft.manual["content_html"],
                    content_json=draft.manual["content_json"],
                    source="ai",
                    revision=1,
                    is_confirmed=False,
                )
                db.add(manual)

            project.flow_status = "draft_ready"
            project.current_step = max(project.current_step, 2)
            project.updated_at = datetime.utcnow()

            job.status = "succeeded"
            job.progress = 100
            job.current_step = "已完成"
            job.result_payload = {
                "software_info_generated": True,
                "manual_generated": True,
                "project_flow_status": project.flow_status,
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
        """执行导出任务（生成下载内容并保存到任务结果）."""
        job.status = "running"
        job.progress = 15
        job.current_step = "合规检查"
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        await db.commit()

        try:
            result = await db.execute(
                select(CopyrightData).where(CopyrightData.project_id == project.id)
            )
            copyright_data = result.scalar_one_or_none()
            if not copyright_data:
                raise ValueError("请先生成软件信息")

            result = await db.execute(
                select(CodeBundle).where(CodeBundle.copyright_data_id == copyright_data.id)
            )
            code_bundle = result.scalar_one_or_none()
            if not code_bundle:
                raise ValueError("请先上传源代码")

            result = await db.execute(
                select(CopyrightManual).where(
                    CopyrightManual.copyright_data_id == copyright_data.id
                )
            )
            manual = result.scalars().first()

            compliance_report = self.compliance_checker.check(
                project_id=project.id,
                software_info={
                    "software_full_name": copyright_data.software_full_name,
                    "version_number": copyright_data.version_number,
                    "development_language": copyright_data.development_language,
                },
                code_bundle={
                    "total_lines": code_bundle.total_lines,
                    "has_enough_code": code_bundle.has_enough_code,
                    "pages_data": code_bundle.pages_data,
                },
                manual={
                    "page_count": manual.page_count if manual else 0,
                    "has_toc": manual.has_toc if manual else False,
                    "has_chapters": manual.has_chapters if manual else False,
                }
                if manual
                else None,
            )
            if not compliance_report.can_export:
                raise ValueError("合规检查未通过，请先修复告警后重试")

            job.progress = 60
            job.current_step = "生成导出包"
            job.updated_at = datetime.utcnow()
            await db.commit()

            export_config = ExportConfig(
                software_name=copyright_data.software_full_name,
                version=copyright_data.version_number,
                applicant_name=project.subject_name or "申请人",
                completion_date=project.completion_date.isoformat()
                if project.completion_date
                else datetime.utcnow().strftime("%Y-%m-%d"),
                first_publication_date=project.first_publication_date.isoformat()
                if project.first_publication_date
                else None,
            )
            export_result = self.export_generator.generate_export_package(
                config=export_config,
                software_info={
                    "software_full_name": copyright_data.software_full_name,
                    "software_short_name": copyright_data.software_short_name,
                    "version_number": copyright_data.version_number,
                    "development_language": copyright_data.development_language,
                    "development_environment": copyright_data.development_environment,
                    "runtime_environment": copyright_data.runtime_environment,
                    "code_line_count": copyright_data.code_line_count,
                    "functional_description": copyright_data.functional_description or "",
                    "technical_features": copyright_data.technical_features or "",
                    "target_domain": copyright_data.target_domain,
                },
                code_pages=code_bundle.pages_data,
                manual={"title": manual.title, "content_html": manual.content_html or ""}
                if manual
                else None,
            )

            project.flow_status = "export_ready"
            project.current_step = 5
            project.updated_at = datetime.utcnow()

            job.status = "succeeded"
            job.progress = 100
            job.current_step = "已完成"
            job.result_payload = {
                "file_name": export_result.file_name,
                "file_size": export_result.file_size,
                "download_url": f"/api/v1/copyright/export-jobs/{job.id}/download",
                "generated_at": export_result.generated_at.isoformat(),
                "content_hex": export_result.content.hex(),
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

    @staticmethod
    def _fill_blank_software_info(copyright_data: CopyrightData, payload: dict) -> None:
        for field_name, field_value in payload.items():
            if not hasattr(copyright_data, field_name):
                continue
            current_value = getattr(copyright_data, field_name)
            if current_value is None or current_value == "":
                setattr(copyright_data, field_name, field_value)

    @staticmethod
    def _overwrite_software_info(copyright_data: CopyrightData, payload: dict) -> None:
        for field_name, field_value in payload.items():
            if hasattr(copyright_data, field_name):
                setattr(copyright_data, field_name, field_value)

