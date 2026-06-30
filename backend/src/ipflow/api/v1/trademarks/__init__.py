"""商标 API 模块.

提供商标相关的 API 接口。
"""

from fastapi import APIRouter

from ipflow.api.v1.trademarks.trademark_info import router as trademark_info_router
from ipflow.api.v1.trademarks.nice_classification import (
    global_router as nice_classification_global_router,
    router as nice_classification_router,
)
from ipflow.api.v1.trademarks.export import router as export_router
from ipflow.api.v1.trademarks.generation_jobs import router as generation_jobs_router
from ipflow.api.v1.trademarks.export_jobs import router as export_jobs_router

router = APIRouter(prefix="/trademarks", tags=["商标"])
router.include_router(trademark_info_router, prefix="/projects/{project_id}")
# 全局尼斯分类查询端点（/nice-classes、/nice-classes/by-id/{id}）不应依赖 project_id，
# 故以无前缀挂载；项目级 selected 端点仍挂到 /projects/{project_id} 下。
router.include_router(nice_classification_global_router)
router.include_router(nice_classification_router, prefix="/projects/{project_id}")
router.include_router(export_router, prefix="/projects/{project_id}")
router.include_router(generation_jobs_router)
router.include_router(export_jobs_router)

__all__ = ["router"]
