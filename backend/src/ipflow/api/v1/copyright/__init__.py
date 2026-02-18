"""软著 API 模块."""

from fastapi import APIRouter

from ipflow.api.v1.copyright.software_info import router as software_info_router
from ipflow.api.v1.copyright.code_bundles import router as code_bundles_router
from ipflow.api.v1.copyright.manuals import router as manuals_router
from ipflow.api.v1.copyright.export import router as export_router

router = APIRouter(prefix="/copyright", tags=["软著"])
router.include_router(software_info_router, prefix="/projects/{project_id}")
router.include_router(code_bundles_router, prefix="/projects/{project_id}")
router.include_router(manuals_router, prefix="/projects/{project_id}")
router.include_router(export_router, prefix="/projects/{project_id}")

__all__ = ["router"]
