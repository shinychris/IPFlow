"""软著模型测试.

测试 CopyrightData、CodeBundle、CopyrightManual 等模型。
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.models.copyright import (
    CopyrightData,
    CodeBundle,
    CopyrightManual,
    ManualScreenshot,
    ManualTemplateType,
)
from ipflow.models.project import Project, ProjectType, ProjectStatus, SubjectType
from ipflow.models.user import User


class TestManualTemplateType:
    """测试说明书模板类型枚举."""

    def test_enum_values(self):
        """测试模板类型枚举值正确."""
        assert ManualTemplateType.WEB == "web"
        assert ManualTemplateType.MOBILE == "mobile"
        assert ManualTemplateType.ALGORITHM == "algorithm"
        assert ManualTemplateType.SCRIPT == "script"
        assert ManualTemplateType.DESKTOP == "desktop"


class TestCopyrightData:
    """测试软著数据模型."""

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """创建测试用户."""
        user = User(
            id=uuid4(),
            email="test_copyright@example.com",
            username="test_copyright_user",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def test_project(self, db_session: AsyncSession, test_user: User) -> Project:
        """创建测试项目."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="测试软著项目",
            project_type=ProjectType.COPYRIGHT,
            status=ProjectStatus.DRAFT,
            subject_type=SubjectType.INDIVIDUAL,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project

    async def test_create_copyright_data(self, db_session: AsyncSession, test_project: Project):
        """测试创建软著数据."""
        copyright_data = CopyrightData(
            id=uuid4(),
            project_id=test_project.id,
            software_full_name="软著助手软件系统",
            software_short_name="软著助手",
            version_number="V2.0.0",
            development_language="Python, TypeScript",
            development_environment="VS Code, PyCharm",
            runtime_environment="Python 3.12+, Node.js 18+",
            code_line_count=50000,
            functional_description="本软件是一款用于软件著作权申请的专业工具...",
            technical_features="1. 智能代码处理引擎\n2. 自动生成说明书...",
            target_domain="知识产权服务",
        )
        db_session.add(copyright_data)
        await db_session.commit()
        await db_session.refresh(copyright_data)

        assert copyright_data.software_full_name == "软著助手软件系统"
        assert copyright_data.software_short_name == "软著助手"
        assert copyright_data.version_number == "V2.0.0"
        assert copyright_data.development_language == "Python, TypeScript"
        assert copyright_data.code_line_count == 50000

    async def test_copyright_data_relationship(self, db_session: AsyncSession, test_project: Project):
        """测试软著数据与项目的关系."""
        copyright_data = CopyrightData(
            id=uuid4(),
            project_id=test_project.id,
            software_full_name="关系测试软件",
            software_short_name="测试软件",
            version_number="V1.0",
            development_language="Python",
        )
        db_session.add(copyright_data)
        await db_session.commit()

        # 查询验证
        result = await db_session.execute(
            select(CopyrightData).where(CopyrightData.project_id == test_project.id)
        )
        data = result.scalar_one()
        
        assert data is not None
        assert data.software_full_name == "关系测试软件"


class TestCodeBundle:
    """测试代码包模型."""

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """创建测试用户."""
        user = User(
            id=uuid4(),
            email="test_code@example.com",
            username="test_code_user",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def test_project(self, db_session: AsyncSession, test_user: User) -> Project:
        """创建测试项目."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="代码测试项目",
            project_type=ProjectType.COPYRIGHT,
            status=ProjectStatus.DRAFT,
            subject_type=SubjectType.INDIVIDUAL,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project

    @pytest.fixture
    async def test_copyright_data(self, db_session: AsyncSession, test_project: Project) -> CopyrightData:
        """创建测试软著数据."""
        copyright_data = CopyrightData(
            id=uuid4(),
            project_id=test_project.id,
            software_full_name="代码测试软件",
            software_short_name="代码测试",
            version_number="V1.0",
            development_language="Python",
        )
        db_session.add(copyright_data)
        await db_session.commit()
        await db_session.refresh(copyright_data)
        return copyright_data

    async def test_create_code_bundle(self, db_session: AsyncSession, test_copyright_data: CopyrightData):
        """测试创建代码包."""
        code_bundle = CodeBundle(
            id=uuid4(),
            copyright_data_id=test_copyright_data.id,
            original_file_name="source_code.zip",
            original_file_size=1024000,
            total_files=150,
            total_lines=50000,
            processed_lines=3000,
            pages_data=[
                {"page_number": 1, "content": "...", "line_start": 1, "line_end": 50, "section": "front"},
                {"page_number": 60, "content": "...", "line_start": 4951, "line_end": 5000, "section": "back"},
            ],
            language_stats={".py": 2500, ".js": 800, ".ts": 1200, ".vue": 500},
            has_enough_code=True,
            warnings=[],
            processed_file_path="/storage/processed/code_bundle_123.txt",
        )
        db_session.add(code_bundle)
        await db_session.commit()
        await db_session.refresh(code_bundle)

        assert code_bundle.original_file_name == "source_code.zip"
        assert code_bundle.total_files == 150
        assert code_bundle.total_lines == 50000
        assert code_bundle.processed_lines == 3000
        assert code_bundle.has_enough_code is True
        assert code_bundle.language_stats[".py"] == 2500

    async def test_code_bundle_insufficient_code(self, db_session: AsyncSession, test_copyright_data: CopyrightData):
        """测试代码行数不足的警告."""
        code_bundle = CodeBundle(
            id=uuid4(),
            copyright_data_id=test_copyright_data.id,
            original_file_name="small_code.zip",
            original_file_size=10240,
            total_files=5,
            total_lines=500,
            processed_lines=500,
            pages_data=[],
            language_stats={".py": 500},
            has_enough_code=False,
            warnings=["代码总行数不足3000行，建议补充更多代码"],
        )
        db_session.add(code_bundle)
        await db_session.commit()
        await db_session.refresh(code_bundle)

        assert code_bundle.has_enough_code is False
        assert len(code_bundle.warnings) == 1
        assert "不足3000行" in code_bundle.warnings[0]


class TestCopyrightManual:
    """测试说明书模型."""

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """创建测试用户."""
        user = User(
            id=uuid4(),
            email="test_manual@example.com",
            username="test_manual_user",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def test_project(self, db_session: AsyncSession, test_user: User) -> Project:
        """创建测试项目."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="说明书测试项目",
            project_type=ProjectType.COPYRIGHT,
            status=ProjectStatus.DRAFT,
            subject_type=SubjectType.INDIVIDUAL,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project

    @pytest.fixture
    async def test_copyright_data(self, db_session: AsyncSession, test_project: Project) -> CopyrightData:
        """创建测试软著数据."""
        copyright_data = CopyrightData(
            id=uuid4(),
            project_id=test_project.id,
            software_full_name="说明书测试软件",
            software_short_name="说明书测试",
            version_number="V1.0",
            development_language="Python",
        )
        db_session.add(copyright_data)
        await db_session.commit()
        await db_session.refresh(copyright_data)
        return copyright_data

    async def test_create_manual(self, db_session: AsyncSession, test_copyright_data: CopyrightData):
        """测试创建说明书."""
        manual = CopyrightManual(
            id=uuid4(),
            copyright_data_id=test_copyright_data.id,
            template_type=ManualTemplateType.WEB,
            title="软著助手软件操作说明书",
            content_html="<h1>软著助手软件</h1><p>本软件用于...</p>",
            content_json={
                "title": "软著助手软件",
                "sections": [
                    {"title": "软件概述", "content": "..."},
                    {"title": "功能介绍", "content": "..."},
                ]
            },
            word_count=3500,
            page_count=18,
            screenshot_count=5,
            has_toc=True,
            has_chapters=True,
        )
        db_session.add(manual)
        await db_session.commit()
        await db_session.refresh(manual)

        assert manual.template_type == ManualTemplateType.WEB
        assert manual.title == "软著助手软件操作说明书"
        assert manual.word_count == 3500
        assert manual.page_count == 18
        assert manual.has_toc is True
        assert manual.has_chapters is True

    async def test_manual_default_values(self, db_session: AsyncSession, test_copyright_data: CopyrightData):
        """测试说明书默认值."""
        manual = CopyrightManual(
            id=uuid4(),
            copyright_data_id=test_copyright_data.id,
            template_type=ManualTemplateType.MOBILE,
        )
        db_session.add(manual)
        await db_session.commit()
        await db_session.refresh(manual)

        assert manual.title == "软件操作说明书"
        assert manual.screenshot_count == 0
        assert manual.has_toc is False
        assert manual.has_chapters is False
