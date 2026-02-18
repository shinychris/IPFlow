"""限额控制服务.

提供组织资源使用限制检查。
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.models import Organization, Project, FileUpload, OrganizationMember


class QuotaExceededError(Exception):
    """限额超限错误."""
    
    def __init__(self, resource: str, limit: int, current: int):
        self.resource = resource
        self.limit = limit
        self.current = current
        super().__init__(f"{resource} quota exceeded: {current}/{limit}")


class QuotaService:
    """限额服务.
    
    检查组织的资源使用情况，防止超支。
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_project_quota(self, organization_id: UUID) -> bool:
        """检查项目数量限额.
        
        Args:
            organization_id: 组织ID
            
        Returns:
            是否可用
            
        Raises:
            QuotaExceededError: 如果超过限额
        """
        # 获取组织限额
        result = await self.db.execute(
            select(Organization.max_projects).where(Organization.id == organization_id)
        )
        max_projects = result.scalar()
        
        # 统计当前项目数
        result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.organization_id == organization_id,
                Project.deleted_at.is_(None)
            )
        )
        current_count = result.scalar()
        
        if current_count >= max_projects:
            raise QuotaExceededError("projects", max_projects, current_count)
        
        return True
    
    async def check_storage_quota(
        self,
        organization_id: UUID,
        additional_bytes: int = 0
    ) -> bool:
        """检查存储空间限额.
        
        Args:
            organization_id: 组织ID
            additional_bytes: 要添加的字节数
            
        Returns:
            是否可用
            
        Raises:
            QuotaExceededError: 如果超过限额
        """
        # 获取组织限额
        result = await self.db.execute(
            select(Organization.max_storage_bytes).where(Organization.id == organization_id)
        )
        max_bytes = result.scalar()
        
        # 统计当前存储使用
        result = await self.db.execute(
            select(func.sum(FileUpload.file_size)).where(
                FileUpload.project_id.in_(
                    select(Project.id).where(Project.organization_id == organization_id)
                )
            )
        )
        current_bytes = result.scalar() or 0
        
        if current_bytes + additional_bytes > max_bytes:
            raise QuotaExceededError(
                "storage",
                max_bytes,
                current_bytes + additional_bytes
            )
        
        return True
    
    async def check_member_quota(self, organization_id: UUID) -> bool:
        """检查成员数量限额.
        
        Args:
            organization_id: 组织ID
            
        Returns:
            是否可用
            
        Raises:
            QuotaExceededError: 如果超过限额
        """
        # 获取组织限额
        result = await self.db.execute(
            select(Organization.max_members).where(Organization.id == organization_id)
        )
        max_members = result.scalar()
        
        # 统计当前成员数
        result = await self.db.execute(
            select(func.count(OrganizationMember.id)).where(
                OrganizationMember.organization_id == organization_id
            )
        )
        current_count = result.scalar()
        
        if current_count >= max_members:
            raise QuotaExceededError("members", max_members, current_count)
        
        return True
    
    async def get_usage_stats(self, organization_id: UUID) -> dict:
        """获取资源使用统计.
        
        Args:
            organization_id: 组织ID
            
        Returns:
            使用统计
        """
        # 获取组织限额
        result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise ValueError("Organization not found")
        
        # 统计项目数
        result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.organization_id == organization_id,
                Project.deleted_at.is_(None)
            )
        )
        project_count = result.scalar()
        
        # 统计存储使用
        result = await self.db.execute(
            select(func.sum(FileUpload.file_size)).where(
                FileUpload.project_id.in_(
                    select(Project.id).where(Project.organization_id == organization_id)
                )
            )
        )
        storage_bytes = result.scalar() or 0
        
        # 统计成员数
        result = await self.db.execute(
            select(func.count(OrganizationMember.id)).where(
                OrganizationMember.organization_id == organization_id
            )
        )
        member_count = result.scalar()
        
        return {
            "projects": {
                "used": project_count,
                "limit": org.max_projects,
                "remaining": org.max_projects - project_count,
                "percentage": round((project_count / org.max_projects) * 100, 2) if org.max_projects > 0 else 0,
            },
            "storage": {
                "used_bytes": storage_bytes,
                "limit_bytes": org.max_storage_bytes,
                "remaining_bytes": org.max_storage_bytes - storage_bytes,
                "percentage": round((storage_bytes / org.max_storage_bytes) * 100, 2) if org.max_storage_bytes > 0 else 0,
                "used_gb": round(storage_bytes / (1024 ** 3), 2),
                "limit_gb": round(org.max_storage_bytes / (1024 ** 3), 2),
            },
            "members": {
                "used": member_count,
                "limit": org.max_members,
                "remaining": org.max_members - member_count,
                "percentage": round((member_count / org.max_members) * 100, 2) if org.max_members > 0 else 0,
            },
        }
    
    async def check_all_quotas(
        self,
        organization_id: UUID,
        check_project: bool = False,
        check_storage: bool = False,
        check_member: bool = False,
        additional_storage_bytes: int = 0
    ) -> dict:
        """检查所有限额.
        
        Args:
            organization_id: 组织ID
            check_project: 是否检查项目限额
            check_storage: 是否检查存储限额
            check_member: 是否检查成员限额
            additional_storage_bytes: 额外存储需求
            
        Returns:
            检查结果
        """
        results = {
            "projects": {"ok": True, "error": None},
            "storage": {"ok": True, "error": None},
            "members": {"ok": True, "error": None},
        }
        
        if check_project:
            try:
                await self.check_project_quota(organization_id)
            except QuotaExceededError as e:
                results["projects"] = {"ok": False, "error": str(e)}
        
        if check_storage:
            try:
                await self.check_storage_quota(organization_id, additional_storage_bytes)
            except QuotaExceededError as e:
                results["storage"] = {"ok": False, "error": str(e)}
        
        if check_member:
            try:
                await self.check_member_quota(organization_id)
            except QuotaExceededError as e:
                results["members"] = {"ok": False, "error": str(e)}
        
        results["all_ok"] = all(r["ok"] for r in results.values())
        return results
