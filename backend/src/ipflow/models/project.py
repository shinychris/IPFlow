"""项目模型.

定义项目相关的 SQLModel 模型。
"""

from datetime import date, datetime
from typing import Optional, List, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Text, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel, Relationship

from ipflow.models.enums import ProjectType, ProjectStatus, SubjectType


class Project(SQLModel, table=True):
    """项目基础模型.
    
    Attributes:
        id: 项目唯一标识 (UUID)
        owner_id: 项目所有者ID
        organization_id: 组织ID（多租户预留）
        project_type: 项目类型（软著/专利/商标）
        status: 项目状态
        current_step: 当前步骤
        name: 项目名称
        version: 版本号
        description: 项目描述
        subject_type: 主体类型
        subject_name: 权利人名称
        subject_id_number: 证件号
        development_method: 开发方式
        publication_status: 发表状态
        completion_date: 完成日期
        first_publication_date: 首次发表日期
        tags: 标签列表
        metadata: 元数据
        external_system_id: 外部系统ID
        external_status: 外部系统状态
        completeness_score: 完成度评分
        created_at: 创建时间
        updated_at: 更新时间
        deleted_at: 删除时间（软删除）
    """
    
    __tablename__ = "project"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    owner_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False, index=True),
    )
    # organization_id: Optional[UUID] = Field(
    #     default=None,
    #     sa_column=Column(ForeignKey("organization.id"), nullable=True, index=True),
    # )
    organization_id: Optional[UUID] = None  # 暂时禁用，M4 阶段实现多租户时再启用
    
    # 类型与状态
    project_type: ProjectType = Field(
        sa_column=Column(String(20), nullable=False, index=True),
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT,
        sa_column=Column(String(20), nullable=False, index=True),
    )
    current_step: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, default=1),
    )
    
    # 基本信息
    name: str = Field(
        sa_column=Column(String(100), nullable=False),
    )
    version: str = Field(
        default="V1.0",
        sa_column=Column(String(20), nullable=False, default="V1.0"),
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 申请主体信息
    subject_type: SubjectType = Field(
        sa_column=Column(String(20), nullable=False),
    )
    subject_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    subject_id_number: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    
    # 开发信息（软著专用）
    development_method: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )
    publication_status: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )
    completion_date: Optional[date] = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )
    first_publication_date: Optional[date] = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )
    
    # 标签和元数据
    tags: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    meta_info: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSON, nullable=True),
    )
    
    # 外部系统对接
    external_system_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    external_status: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    external_updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    
    # 完成度评分（AI辅助）
    completeness_score: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
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
    
    # 关系（延迟导入避免循环依赖）
    # owner: "User" = Relationship(back_populates="projects")
    # copyright_data: Optional["CopyrightData"] = Relationship(back_populates="project")
    # patent_data: Optional["PatentData"] = Relationship(back_populates="project")
    # trademark_data: Optional["TrademarkData"] = Relationship(back_populates="project")


class ProjectResponse(SQLModel):
    """项目响应模型."""
    
    id: UUID
    owner_id: UUID
    project_type: ProjectType
    status: ProjectStatus
    current_step: int
    name: str
    version: str
    description: Optional[str] = None
    subject_type: SubjectType
    subject_name: Optional[str] = None
    development_method: Optional[str] = None
    publication_status: Optional[str] = None
    completion_date: Optional[date] = None
    first_publication_date: Optional[date] = None
    tags: Optional[List[str]] = None
    completeness_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(SQLModel):
    """创建项目请求模型."""
    
    name: str = Field(..., min_length=1, max_length=100)
    project_type: ProjectType
    subject_type: SubjectType
    version: str = Field(default="V1.0", max_length=20)
    description: Optional[str] = None
    development_method: Optional[str] = None
    publication_status: Optional[str] = None
    subject_name: Optional[str] = None
    subject_id_number: Optional[str] = None


class ProjectUpdate(SQLModel):
    """更新项目请求模型."""
    
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    status: Optional[ProjectStatus] = None
    current_step: Optional[int] = None
    version: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None
    subject_name: Optional[str] = None
    subject_id_number: Optional[str] = None
    completion_date: Optional[date] = None
    first_publication_date: Optional[date] = None
    tags: Optional[List[str]] = None
    meta_info: Optional[dict[str, Any]] = None
