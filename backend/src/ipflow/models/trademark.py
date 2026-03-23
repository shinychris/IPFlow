"""商标模型.

定义商标相关的 SQLModel 模型。
"""

from datetime import datetime, date
from typing import Optional, List, Any
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class TrademarkType(str, Enum):
    """商标类型枚举."""
    
    WORD = "word"              # 文字商标
    DEVICE = "device"          # 图形商标
    COMPOSITE = "composite"    # 组合商标
    THREE_D = "3d"             # 三维商标
    SOUND = "sound"            # 声音商标
    COLOR = "color"            # 颜色商标


class TrademarkStatus(str, Enum):
    """商标状态枚举."""
    
    DRAFT = "draft"                  # 草稿
    PENDING_REVIEW = "pending_review" # 待审核
    UNDER_EXAMINATION = "under_examination"  # 审查中
    PRELIMINARY_APPROVED = "preliminary_approved"  # 初审公告
    REGISTERED = "registered"        # 已注册
    REJECTED = "rejected"            # 被驳回
    OPPOSED = "opposed"              # 被异议
    EXPIRED = "expired"              # 已过期
    CANCELLED = "cancelled"          # 已注销


class TrademarkData(SQLModel, table=True):
    """商标项目详细信息.
    
    Attributes:
        id: 唯一标识
        project_id: 关联项目ID
        trademark_type: 商标类型
        trademark_name: 商标名称/文字
        description: 商标描述
        design_description: 设计说明（图形商标使用）
        color_claim: 颜色说明
        upload_id: 商标图样上传文件ID
    """
    
    __tablename__ = "trademark_data"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    project_id: UUID = Field(
        sa_column=Column(ForeignKey("project.id"), nullable=False, unique=True),
    )
    
    # 商标类型
    trademark_type: TrademarkType = Field(
        sa_column=Column(String(20), nullable=False),
    )
    
    # 商标名称/文字
    trademark_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
    )
    
    # 商标描述
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 设计说明（图形商标）
    design_description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 颜色说明
    color_claim: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 商标图样上传文件ID
    upload_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(ForeignKey("file_upload.id"), nullable=True),
    )
    
    # 商标说明（特殊字体、非规范汉字等）
    special_notes: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 状态
    status: TrademarkStatus = Field(
        default=TrademarkStatus.DRAFT,
        sa_column=Column(String(30), nullable=False, default=TrademarkStatus.DRAFT),
    )
    
    # 外部系统对接
    application_number: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    registration_number: Optional[str] = Field(
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
    registration_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    expiry_date: Optional[date] = Field(
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


class NiceClassification(SQLModel, table=True):
    """尼斯分类.
    
    商标商品/服务分类（基于尼斯协定第11版2025文本）。
    
    Attributes:
        id: 唯一标识
        class_number: 类别号（1-45）
        class_name: 类别名称
        class_name_en: 类别英文名称
        description: 类别说明
    """
    
    __tablename__ = "nice_classification"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    
    # 类别号 1-45
    class_number: int = Field(
        sa_column=Column(Integer, nullable=False, index=True),
    )
    
    # 类别名称
    class_name: str = Field(
        sa_column=Column(String(100), nullable=False),
    )
    
    class_name_en: Optional[str] = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
    )
    
    # 类别说明
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    
    # 是否有效
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, default=True),
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


class TrademarkNiceClass(SQLModel, table=True):
    """商标尼斯分类关联表.
    
    一个商标可以申请多个类别的商品/服务。
    
    Attributes:
        id: 唯一标识
        trademark_data_id: 关联商标数据ID
        nice_class_id: 关联尼斯分类ID
        goods_services: 具体商品/服务项目列表
    """
    
    __tablename__ = "trademark_nice_class"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    trademark_data_id: UUID = Field(
        sa_column=Column(ForeignKey("trademark_data.id"), nullable=False, index=True),
    )
    nice_class_id: UUID = Field(
        sa_column=Column(ForeignKey("nice_classification.id"), nullable=False),
    )
    
    # 具体商品/服务项目
    goods_services: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=list),
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


class TrademarkExportConfig(SQLModel, table=True):
    """商标导出配置.
    
    存储网报系统导出配置等。
    """
    
    __tablename__ = "trademark_export_config"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    trademark_data_id: UUID = Field(
        sa_column=Column(ForeignKey("trademark_data.id"), nullable=False, unique=True),
    )
    
    # 申请人信息
    applicant_info: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    
    # 优先权声明
    priority_claims: Optional[List[dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    
    # 代理信息
    agent_info: Optional[dict[str, Any]] = Field(
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
