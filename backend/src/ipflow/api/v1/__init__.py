"""API v1 路由聚合."""

from fastapi import APIRouter

from ipflow.api.v1.auth import router as auth_router
from ipflow.api.v1.projects import router as projects_router
from ipflow.api.v1.uploads import router as uploads_router
from ipflow.api.v1.copyright import router as copyright_router
from ipflow.api.v1.compliance import router as compliance_router
from ipflow.api.v1.organizations import router as organizations_router
from ipflow.api.v1.subscriptions import router as subscriptions_router
from ipflow.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(uploads_router)
api_router.include_router(copyright_router)
api_router.include_router(compliance_router)
api_router.include_router(organizations_router)
api_router.include_router(subscriptions_router)
api_router.include_router(admin_router)
