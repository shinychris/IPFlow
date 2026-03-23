"""专利模型.

定义专利相关的 SQLModel 模型。
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class PatentType(str, Enum):
    """专利类型枚举."""
    
    INVENTION = "invention"          # 发明专利
    UTILITY_MODEL = "utility_model"  # 实用新型
    DESIGN = "design"                # 外观设计


class PatentStatus(str, Enum):
    """专利状态枚举."""
    
    DRAFT = "draft"                  # 草稿
    PENDING_REVIEW = "pending_review" # 待审核
    UNDER_EXAMINATION = "under_examination"  # 审查中
    GRANTED = "granted"              # 已授权
    REJECTED = "rejected"            # 被驳回
    WITHDRAWN = "withdrawn"          # 已撤回
    EXPIRED = "expired"              # 已过期


class PatentData(SQLModel, table=True):
    """专利项目详细信息.
    
    Attributes:
        id: 唯一标识
        project_id: 关联项目ID
        patent_type: 专利类型
        title: 专利名称
        technical_field: 技术领域
        background_art: 背景技术
        invention_content: 发明内容
        implementation: 具体实施方式
        abstract: 摘要
        abstract_figure: 摘要附图编号
        claims_count: 权利要求数量
        drawings_count: 附图数量
    """
    
    __tablename__ = "patent_data"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    project_id: UUID = Field(
        sa_column=Column(ForeignKey("project.id"), nullable=False, unique=True),
    )
    
    # 专利类型
    patent_type: PatentType = Field(
        sa_column=Column(String(20), nullable=False),
    )
    
    # 基本信息
    title: str = Field(
        sa_column=Column(String(200), nullable=False),
    )
    
    # 技术领域
    technical_field: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 背景技术
    background_art: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 发明内容（解决的问题、技术方案、有益效果）
    invention_content: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    
    # 具体实施方式
    implementation: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 摘要
    abstract: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 摘要附图
    abstract_figure_number: Optional[str] = Field(
        default=None,
        sa_column=Column(String(10), nullable=True),
    )
    
    # 统计信息
    claims_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
    )
    drawings_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
    )
    
    # 状态
    status: PatentStatus = Field(
        default=PatentStatus.DRAFT,
        sa_column=Column(String(30), nullable=False, default=PatentStatus.DRAFT),
    )
    
    # 外部系统对接
    application_number: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    publication_number: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    grant_number: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    source: str = Field(
        default="human",
        sa_column=Column(String(20), nullable=False, default="human"),
    )
    revision: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, default=1),
    )
    is_confirmed: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    last_edited_by: Optional[UUID] = Field(
        default=None,
        sa_column=Column(ForeignKey("user.id"), nullable=True),
    )
    
    # 时间戳
    filing_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    publication_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    grant_date: Optional[datetime] = Field(
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


class PatentClaim(SQLModel, table=True):
    """专利权利要求书.
    
    Attributes:
        id: 唯一标识
        patent_data_id: 关联专利数据ID
        claim_number: 权利要求编号
        claim_type: 类型（独立/从属）
        parent_claim: 引用权利要求（从属权利要求使用）
        content: 权利要求内容
    """
    
    __tablename__ = "patent_claim"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    patent_data_id: UUID = Field(
        sa_column=Column(ForeignKey("patent_data.id"), nullable=False, index=True),
    )
    
    # 权利要求编号
    claim_number: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    
    # 权利要求类型
    claim_type: str = Field(
        default="independent",
        sa_column=Column(String(20), nullable=False, default="independent"),
    )  # independent 或 dependent
    
    # 从属权利要求引用的权利要求编号
    parent_claim_number: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    
    # 内容
    content: str = Field(
        sa_column=Column(Text, nullable=False),
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


class PatentDrawing(SQLModel, table=True):
    """专利附图.
    
    Attributes:
        id: 唯一标识
        patent_data_id: 关联专利数据ID
        figure_number: 图号
        figure_title: 图题
        description: 简要说明
        upload_id: 关联上传文件ID
    """
    
    __tablename__ = "patent_drawing"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    patent_data_id: UUID = Field(
        sa_column=Column(ForeignKey("patent_data.id"), nullable=False, index=True),
    )
    
    # 图号（如 "图1", "图2"）
    figure_number: str = Field(
        sa_column=Column(String(10), nullable=False),
    )
    
    # 图题
    figure_title: Optional[str] = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
    )
    
    # 简要说明
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 关联上传文件
    upload_id: UUID = Field(
        sa_column=Column(ForeignKey("file_upload.id"), nullable=False),
    )
    
    # 显示顺序
    display_order: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
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


class PatentExportConfig(SQLModel, table=True):
    """专利导出配置.
    
    存储 CPC 客户端导出配置等。
    """
    
    __tablename__ = "patent_export_config"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    patent_data_id: UUID = Field(
        sa_column=Column(ForeignKey("patent_data.id"), nullable=False, unique=True),
    )
    
    # CPC 客户端配置
    inventor_list: List[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=list),
    )
    applicant_info: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    agent_info: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    priority_claims: Optional[List[dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
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
