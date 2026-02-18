"""组织管理 API.

提供组织的 CRUD 和成员管理功能。
"""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import Organization, OrganizationMember, OrganizationInvitation, User, UserRole
from ipflow.models.user import UserStatus
from ipflow.api.deps import require_active_user, require_admin_user
from ipflow.core.tenant import TenantService

router = APIRouter(prefix="/organizations", tags=["组织"])


# =============================================================================
# 请求/响应模型
# =============================================================================

class OrganizationBase(BaseModel):
    """组织基础模型."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    business_type: Optional[str] = None
    license_number: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """创建组织请求."""
    pass


class OrganizationUpdate(BaseModel):
    """更新组织请求."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class OrganizationResponse(BaseModel):
    """组织响应."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    business_type: Optional[str]
    plan_type: str
    max_projects: int
    max_storage_bytes: int
    max_members: int
    used_storage_bytes: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    """成员响应."""
    id: UUID
    user_id: UUID
    username: str
    email: str
    display_name: Optional[str]
    role: str
    joined_at: datetime


class InviteMemberRequest(BaseModel):
    """邀请成员请求."""
    email: EmailStr
    role: UserRole = UserRole.MEMBER


class UpdateMemberRoleRequest(BaseModel):
    """更新成员角色请求."""
    role: UserRole


# =============================================================================
# API 端点
# =============================================================================

@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[Organization]:
    """获取当前用户的组织列表."""
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(
            OrganizationMember.user_id == current_user.id,
            Organization.is_active == True,
            Organization.deleted_at.is_(None),
        )
        .order_by(Organization.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """创建新组织."""
    # 检查 slug 是否已存在
    result = await db.execute(
        select(Organization).where(Organization.slug == data.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="组织标识已被使用",
        )
    
    # 创建组织
    org = Organization(
        id=uuid4(),
        name=data.name,
        slug=data.slug,
        description=data.description,
        business_type=data.business_type,
        license_number=data.license_number,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        plan_type="free",
        max_projects=10,
        max_storage_bytes=1073741824,  # 1GB
        max_members=5,
    )
    db.add(org)
    await db.flush()  # 获取 org.id
    
    # 创建者为管理员
    member = OrganizationMember(
        id=uuid4(),
        organization_id=org.id,
        user_id=current_user.id,
        role=UserRole.ADMIN,
    )
    db.add(member)
    await db.commit()
    await db.refresh(org)
    
    return org


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """获取组织详情."""
    # 检查用户是否在组织中
    tenant_service = TenantService(db)
    if not await tenant_service.check_user_in_organization(current_user.id, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该组织",
        )
    
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_active == True,
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组织不存在",
        )
    
    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """更新组织信息."""
    # 检查权限（需要管理员）
    tenant_service = TenantService(db)
    role = await tenant_service.get_user_role_in_organization(current_user.id, org_id)
    
    if role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_active == True,
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组织不存在",
        )
    
    # 更新字段
    if data.name is not None:
        org.name = data.name
    if data.description is not None:
        org.description = data.description
    if data.contact_email is not None:
        org.contact_email = data.contact_email
    if data.contact_phone is not None:
        org.contact_phone = data.contact_phone
    
    org.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(org)
    
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除组织（软删除）."""
    # 检查权限
    tenant_service = TenantService(db)
    role = await tenant_service.get_user_role_in_organization(current_user.id, org_id)
    
    if role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_active == True,
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组织不存在",
        )
    
    # 软删除
    org.is_active = False
    org.deleted_at = datetime.utcnow()
    await db.commit()


# =============================================================================
# 成员管理
# =============================================================================

@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_members(
    org_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """获取组织成员列表."""
    # 检查用户是否在组织中
    tenant_service = TenantService(db)
    if not await tenant_service.check_user_in_organization(current_user.id, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该组织",
        )
    
    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, OrganizationMember.user_id == User.id)
        .where(OrganizationMember.organization_id == org_id)
        .order_by(OrganizationMember.joined_at.desc())
    )
    
    members = []
    for member, user in result.all():
        members.append({
            "id": member.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": member.role.value,
            "joined_at": member.joined_at,
        })
    
    return members


@router.post("/{org_id}/invite", response_model=dict)
async def invite_member(
    org_id: UUID,
    data: InviteMemberRequest,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """邀请成员加入组织."""
    # 检查权限
    tenant_service = TenantService(db)
    role = await tenant_service.get_user_role_in_organization(current_user.id, org_id)
    
    if role not in [UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员或经理权限",
        )
    
    # 检查组织是否存在
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_active == True,
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组织不存在",
        )
    
    # 检查成员数量限制
    result = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == org_id
        )
    )
    member_count = result.scalar()
    
    if member_count >= org.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="组织成员数量已达上限",
        )
    
    # 生成邀请令牌
    token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation(
        id=uuid4(),
        organization_id=org_id,
        inviter_id=current_user.id,
        email=data.email,
        role=data.role,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invitation)
    await db.commit()
    
    # TODO: 发送邀请邮件
    
    return {
        "message": "邀请已发送",
        "email": data.email,
        "expires_at": invitation.expires_at.isoformat(),
    }


@router.patch("/{org_id}/members/{member_id}", response_model=MemberResponse)
async def update_member_role(
    org_id: UUID,
    member_id: UUID,
    data: UpdateMemberRoleRequest,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新成员角色."""
    # 检查权限
    tenant_service = TenantService(db)
    role = await tenant_service.get_user_role_in_organization(current_user.id, org_id)
    
    if role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id,
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )
    
    member.role = data.role
    await db.commit()
    
    # 获取更新后的成员信息
    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, OrganizationMember.user_id == User.id)
        .where(OrganizationMember.id == member_id)
    )
    member, user = result.first()
    
    return {
        "id": member.id,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "role": member.role.value,
        "joined_at": member.joined_at,
    }


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """移除成员."""
    # 检查权限
    tenant_service = TenantService(db)
    role = await tenant_service.get_user_role_in_organization(current_user.id, org_id)
    
    # 管理员可以移除任何人，成员只能移除自己
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id,
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )
    
    if role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        if member.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能移除自己",
            )
    
    await db.delete(member)
    await db.commit()


@router.post("/join/{token}", response_model=dict)
async def join_organization(
    token: str,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """通过邀请链接加入组织."""
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.token == token,
            OrganizationInvitation.accepted_at.is_(None),
        )
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邀请链接无效",
        )
    
    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请链接已过期",
        )
    
    # 检查邮箱是否匹配
    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="邀请邮箱与当前用户不匹配",
        )
    
    # 检查是否已在组织中
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经是组织成员",
        )
    
    # 添加成员
    member = OrganizationMember(
        id=uuid4(),
        organization_id=invitation.organization_id,
        user_id=current_user.id,
        role=invitation.role,
    )
    db.add(member)
    
    # 标记邀请为已接受
    invitation.accepted_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "成功加入组织",
        "organization_id": str(invitation.organization_id),
    }
