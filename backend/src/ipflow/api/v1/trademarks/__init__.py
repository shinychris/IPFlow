"""商标 API 模块.

提供商标相关的 API 接口。
"""

from fastapi import APIRouter

from ipflow.api.v1.trademarks.trademark_info import router as trademark_info_router
from ipflow.api.v1.trademarks.nice_classification import router as nice_classification_router
from ipflow.api.v1.trademarks.export import router as export_router

router = APIRouter(prefix="/trademarks", tags=["商标"])
router.include_router(trademark_info_router, prefix="/projects/{project_id}")
router.include_router(nice_classification_router, prefix="/projects/{project_id}")
router.include_router(export_router, prefix="/projects/{project_id}")

__all__ = ["router"]
