"""用户模型.

定义用户相关的 SQLModel 模型。
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, DateTime
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """用户角色枚举."""
    
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """用户状态枚举."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(SQLModel, table=True):
    """用户模型.
    
    Attributes:
        id: 用户唯一标识 (UUID)
        email: 邮箱地址，唯一
        username: 用户名，唯一
        hashed_password: 密码哈希
        display_name: 显示名称
        avatar_url: 头像 URL
        phone: 手机号
        role: 用户角色
        status: 用户状态
        is_verified: 是否验证邮箱
        last_login_at: 最后登录时间
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "user"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    email: str = Field(
        sa_column=Column(String(255), unique=True, nullable=False, index=True),
    )
    username: str = Field(
        sa_column=Column(String(50), unique=True, nullable=False, index=True),
    )
    hashed_password: str = Field(
        sa_column=Column(String(255), nullable=False),
    )
    display_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    avatar_url: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
    )
    phone: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        sa_column=Column(String(20), nullable=False),
    )
    status: UserStatus = Field(
        default=UserStatus.PENDING,
        sa_column=Column(String(20), nullable=False),
    )
    is_verified: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )


class UserResponse(SQLModel):
    """用户响应模型（不包含敏感信息）."""
    
    id: UUID
    email: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
