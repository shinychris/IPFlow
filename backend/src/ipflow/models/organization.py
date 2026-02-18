"""组织模型.

定义组织和成员关系的 SQLModel 模型。
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlmodel import Field, SQLModel, Relationship

from ipflow.models.user import UserRole


class Organization(SQLModel, table=True):
    """组织/企业模型（多租户核心）.
    
    Attributes:
        id: 组织唯一标识
        name: 组织名称
        slug: 组织标识（URL友好）
        description: 组织描述
        business_type: 业务类型（企业、个人、事务所）
        license_number: 营业执照号
        contact_email: 联系邮箱
        contact_phone: 联系电话
        plan_type: 订阅计划类型
        plan_expires_at: 订阅过期时间
        max_projects: 最大项目数
        max_storage_bytes: 最大存储空间（字节）
        max_members: 最大成员数
        used_storage_bytes: 已使用存储空间
        is_active: 是否激活
        is_verified: 是否已验证
        created_at: 创建时间
        updated_at: 更新时间
        deleted_at: 删除时间（软删除）
    """
    
    __tablename__ = "organization"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    
    # 基本信息
    name: str = Field(
        sa_column=Column(String(100), nullable=False),
    )
    slug: str = Field(
        sa_column=Column(String(50), unique=True, nullable=False, index=True),
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 商业信息
    business_type: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )  # enterprise, individual, agency
    license_number: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    contact_email: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), nullable=True),
    )
    contact_phone: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )
    
    # 订阅与限额
    plan_type: str = Field(
        default="free",
        sa_column=Column(String(20), nullable=False, default="free"),
    )  # free, pro, enterprise
    plan_expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    max_projects: int = Field(
        default=10,
        sa_column=Column(Integer, nullable=False, default=10),
    )
    max_storage_bytes: int = Field(
        default=1073741824,  # 1GB
        sa_column=Column(BigInteger, nullable=False, default=1073741824),
    )
    max_members: int = Field(
        default=5,
        sa_column=Column(Integer, nullable=False, default=5),
    )
    used_storage_bytes: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
    )
    
    # 状态
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, default=True),
    )
    is_verified: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    
    # 时间戳
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    
    # 计算属性
    @property
    def storage_usage_percent(self) -> float:
        """计算存储使用率."""
        if self.max_storage_bytes == 0:
            return 0.0
        return (self.used_storage_bytes / self.max_storage_bytes) * 100
    
    @property
    def is_plan_expired(self) -> bool:
        """检查订阅是否过期."""
        if self.plan_expires_at is None:
            return False
        return datetime.utcnow() > self.plan_expires_at


class OrganizationMember(SQLModel, table=True):
    """组织成员关系模型.
    
    Attributes:
        id: 关系唯一标识
        organization_id: 组织ID
        user_id: 用户ID
        role: 成员角色
        joined_at: 加入时间
    """
    
    __tablename__ = "organization_member"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    organization_id: UUID = Field(
        sa_column=Column(ForeignKey("organization.id"), nullable=False, index=True),
    )
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False, index=True),
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        sa_column=Column(String(20), nullable=False),
    )
    joined_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )


class OrganizationInvitation(SQLModel, table=True):
    """组织邀请模型.
    
    Attributes:
        id: 邀请唯一标识
        organization_id: 组织ID
        inviter_id: 邀请人ID
        email: 被邀请人邮箱
        role: 邀请角色
        token: 邀请令牌
        expires_at: 过期时间
        accepted_at: 接受时间
        created_at: 创建时间
    """
    
    __tablename__ = "organization_invitation"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    organization_id: UUID = Field(
        sa_column=Column(ForeignKey("organization.id"), nullable=False),
    )
    inviter_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False),
    )
    email: str = Field(
        sa_column=Column(String(255), nullable=False),
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        sa_column=Column(String(20), nullable=False),
    )
    token: str = Field(
        sa_column=Column(String(100), unique=True, nullable=False, index=True),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False),
    )
    accepted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    
    @property
    def is_expired(self) -> bool:
        """检查邀请是否过期."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_accepted(self) -> bool:
        """检查邀请是否已接受."""
        return self.accepted_at is not None
