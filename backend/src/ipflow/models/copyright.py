"""软著模型.

定义软件著作权相关的 SQLModel 模型。
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

# 重导出说明书模板类型枚举，便于 `from ipflow.models.copyright import ManualTemplateType`
# （该枚举统一定义在 enums.py，避免多处重复定义）
from ipflow.models.enums import ManualTemplateType  # noqa: E402,F401


class CopyrightData(SQLModel, table=True):
    """软著项目详细信息.
    
    Attributes:
        id: 唯一标识
        project_id: 关联项目ID
        software_full_name: 软件全称
        software_short_name: 软件简称
        version_number: 版本号
        development_language: 开发语言
        development_environment: 开发环境
        runtime_environment: 运行环境
        code_line_count: 代码行数
        functional_description: 功能描述
        technical_features: 技术特点
        target_domain: 面向领域
    """
    
    __tablename__ = "copyright_data"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    project_id: UUID = Field(
        sa_column=Column(ForeignKey("project.id"), nullable=False, unique=True),
    )
    
    # 软件基本信息
    software_full_name: str = Field(
        sa_column=Column(String(100), nullable=False),
    )
    software_short_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    version_number: str = Field(
        sa_column=Column(String(20), nullable=False),
    )
    
    # 技术信息
    development_language: str = Field(
        sa_column=Column(String(100), nullable=False),
    )
    development_environment: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    runtime_environment: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    code_line_count: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    
    # 功能描述
    functional_description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    technical_features: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    target_domain: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
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
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    
    # 关系
    # project: "Project" = Relationship(back_populates="copyright_data")
    # code_bundles: List["CodeBundle"] = Relationship(back_populates="copyright_data")
    # manuals: List["CopyrightManual"] = Relationship(back_populates="copyright_data")


class CodeBundle(SQLModel, table=True):
    """代码包（处理后的源代码）.
    
    Attributes:
        id: 唯一标识
        copyright_data_id: 关联软著数据ID
        upload_id: 关联上传文件ID
        original_file_name: 原始文件名
        original_file_size: 原始文件大小（字节）
        total_files: 总文件数
        total_lines: 总行数
        processed_lines: 处理后用于生成文档的行数
        pages_data: 分页数据（JSON数组）
        language_stats: 语言统计（JSON对象）
        has_enough_code: 是否有足够代码（3000+行）
        warnings: 警告信息列表
        processed_file_path: 处理后文件存储路径
    """
    
    __tablename__ = "code_bundle"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    copyright_data_id: UUID = Field(
        sa_column=Column(ForeignKey("copyright_data.id"), nullable=False, index=True),
    )
    upload_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(ForeignKey("file_upload.id"), nullable=True),
    )
    
    # 原始文件信息
    original_file_name: str = Field(
        sa_column=Column(String(255), nullable=False),
    )
    original_file_size: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    
    # 处理结果
    total_files: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    total_lines: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    processed_lines: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    
    # 代码页数据（结构化存储）
    pages_data: List[dict[str, Any]] = Field(
        sa_column=Column(JSON, nullable=False, default=list),
    )
    
    # 文件类型统计
    language_stats: dict[str, int] = Field(
        sa_column=Column(JSON, nullable=False, default=dict),
    )
    
    # 合规状态
    has_enough_code: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    
    # 存储路径
    processed_file_path: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
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
    
    # 关系
    # copyright_data: CopyrightData = Relationship(back_populates="code_bundles")


class CopyrightManual(SQLModel, table=True):
    """软著操作说明书.
    
    Attributes:
        id: 唯一标识
        copyright_data_id: 关联软著数据ID
        template_type: 模板类型
        title: 说明书标题
        content_html: HTML内容
        content_json: 结构化内容（JSON）
        word_count: 字数
        page_count: 页数
        screenshot_count: 截图数量
        has_toc: 是否有目录
        has_chapters: 是否有规范章节
    """
    
    __tablename__ = "copyright_manual"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    copyright_data_id: UUID = Field(
        sa_column=Column(ForeignKey("copyright_data.id"), nullable=False, index=True),
    )
    
    # 模板信息
    template_type: str = Field(
        sa_column=Column(String(20), nullable=False),
    )
    
    # 内容
    title: str = Field(
        default="软件操作说明书",
        sa_column=Column(String(100), nullable=False, default="软件操作说明书"),
    )
    content_html: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    content_json: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    
    # 统计
    word_count: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    page_count: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    screenshot_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
    )
    
    # 合规检查
    has_toc: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    has_chapters: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
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
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    
    # 关系
    # copyright_data: CopyrightData = Relationship(back_populates="manuals")
    # screenshots: List["ManualScreenshot"] = Relationship(back_populates="manual")


class ManualScreenshot(SQLModel, table=True):
    """说明书截图.
    
    Attributes:
        id: 唯一标识
        manual_id: 关联说明书ID
        upload_id: 关联上传文件ID
        caption: 图注
        display_order: 显示顺序
    """
    
    __tablename__ = "manual_screenshot"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    manual_id: UUID = Field(
        sa_column=Column(ForeignKey("copyright_manual.id"), nullable=False, index=True),
    )
    upload_id: UUID = Field(
        sa_column=Column(ForeignKey("file_upload.id"), nullable=False),
    )
    
    caption: Optional[str] = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
    )
    display_order: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
    )
    
    # 时间戳
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    
    # 关系
    # manual: CopyrightManual = Relationship(back_populates="screenshots")


class FileUpload(SQLModel, table=True):
    """文件上传记录.
    
    Attributes:
        id: 唯一标识
        project_id: 关联项目ID
        uploaded_by: 上传者ID
        original_name: 原始文件名
        storage_name: 存储文件名（UUID）
        storage_path: 存储路径
        file_size: 文件大小（字节）
        mime_type: MIME类型
        checksum: SHA-256校验和
        file_category: 文件分类（code, proof, manual, drawing）
        file_type: 文件类型（identity, contract等）
        processing_status: 处理状态
        processing_result: 处理结果（JSON）
    """
    
    __tablename__ = "file_upload"
    
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    project_id: UUID = Field(
        sa_column=Column(ForeignKey("project.id"), nullable=False, index=True),
    )
    uploaded_by: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False),
    )
    
    # 文件信息
    original_name: str = Field(
        sa_column=Column(String(255), nullable=False),
    )
    storage_name: str = Field(
        sa_column=Column(String(255), nullable=False),
    )
    storage_path: str = Field(
        sa_column=Column(String(500), nullable=False),
    )
    file_size: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    mime_type: str = Field(
        sa_column=Column(String(100), nullable=False),
    )
    checksum: str = Field(
        sa_column=Column(String(64), nullable=False),
    )
    
    # 分类
    file_category: str = Field(
        sa_column=Column(String(50), nullable=False),
    )
    file_type: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    
    # 处理状态
    processing_status: str = Field(
        default="pending",
        sa_column=Column(String(20), nullable=False, default="pending"),
    )
    processing_result: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    
    # 时间戳
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )


class CopyrightGenerationJob(SQLModel, table=True):
    """软著生成与导出任务."""

    __tablename__ = "copyright_generation_job"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(
        sa_column=Column(ForeignKey("project.id"), nullable=False, index=True),
    )
    project_type: str = Field(
        default="copyright",
        sa_column=Column(String(20), nullable=False, index=True, default="copyright"),
    )
    job_domain: str = Field(
        default="copyright",
        sa_column=Column(String(20), nullable=False, index=True, default="copyright"),
    )
    job_type: str = Field(
        default="ai_draft",
        sa_column=Column(String(20), nullable=False, index=True, default="ai_draft"),
    )
    status: str = Field(
        default="queued",
        sa_column=Column(String(20), nullable=False, index=True, default="queued"),
    )
    progress: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
    )
    current_step: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    input_payload: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    result_payload: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    retry_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
    )
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    finished_at: Optional[datetime] = Field(
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
