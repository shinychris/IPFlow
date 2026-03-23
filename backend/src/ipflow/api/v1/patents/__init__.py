"""专利 API 模块.

提供专利相关的 API 接口。
"""

from fastapi import APIRouter

from ipflow.api.v1.patents.patent_info import router as patent_info_router
from ipflow.api.v1.patents.claims import router as claims_router
from ipflow.api.v1.patents.description import router as description_router
from ipflow.api.v1.patents.export import router as export_router
from ipflow.api.v1.patents.generation_jobs import router as generation_jobs_router
from ipflow.api.v1.patents.export_jobs import router as export_jobs_router

router = APIRouter(prefix="/patents", tags=["专利"])
router.include_router(patent_info_router, prefix="/projects/{project_id}")
router.include_router(claims_router, prefix="/projects/{project_id}")
router.include_router(description_router, prefix="/projects/{project_id}")
router.include_router(export_router, prefix="/projects/{project_id}")
router.include_router(generation_jobs_router)
router.include_router(export_jobs_router)

__all__ = ["router"]
