"""项目模型测试.

测试 Project 模型及其相关功能。
"""

from datetime import date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.models.project import Project, ProjectType, ProjectStatus, SubjectType
from ipflow.models.user import User


class TestProjectType:
    """测试项目类型枚举."""

    def test_enum_values(self):
        """测试枚举值正确."""
        assert ProjectType.COPYRIGHT == "copyright"
        assert ProjectType.PATENT == "patent"
        assert ProjectType.TRADEMARK == "trademark"


class TestProjectStatus:
    """测试项目状态枚举."""

    def test_enum_values(self):
        """测试状态枚举值正确."""
        assert ProjectStatus.DRAFT == "draft"
        assert ProjectStatus.IN_PROGRESS == "in_progress"
        assert ProjectStatus.REVIEWING == "reviewing"
        assert ProjectStatus.PENDING_SUBMIT == "pending_submit"
        assert ProjectStatus.SUBMITTED == "submitted"
        assert ProjectStatus.ACCEPTED == "accepted"
        assert ProjectStatus.APPROVED == "approved"
        assert ProjectStatus.REJECTED == "rejected"
        assert ProjectStatus.WITHDRAWN == "withdrawn"


class TestSubjectType:
    """测试主体类型枚举."""

    def test_enum_values(self):
        """测试主体类型枚举值正确."""
        assert SubjectType.INDIVIDUAL == "individual"
        assert SubjectType.ENTERPRISE == "enterprise"
        assert SubjectType.INSTITUTION == "institution"
        assert SubjectType.AGENCY == "agency"


class TestProjectModel:
    """测试项目模型."""

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """创建测试用户."""
        user = User(
            id=uuid4(),
            email="test_project@example.com",
            username="test_project_user",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_create_project(self, db_session: AsyncSession, test_user: User):
        """测试创建项目."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="测试软著项目",
            project_type=ProjectType.COPYRIGHT,
            status=ProjectStatus.DRAFT,
            subject_type=SubjectType.INDIVIDUAL,
            version="V1.0",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.name == "测试软著项目"
        assert project.project_type == ProjectType.COPYRIGHT
        assert project.status == ProjectStatus.DRAFT
        assert project.owner_id == test_user.id
        assert project.current_step == 1
        assert project.version == "V1.0"

    async def test_project_default_values(self, db_session: AsyncSession, test_user: User):
        """测试项目默认值."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="默认测试项目",
            project_type=ProjectType.PATENT,
            subject_type=SubjectType.ENTERPRISE,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.status == ProjectStatus.DRAFT
        assert project.current_step == 1
        assert project.version == "V1.0"

    async def test_project_relationship_with_user(self, db_session: AsyncSession, test_user: User):
        """测试项目与用户的关系."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="关系测试项目",
            project_type=ProjectType.TRADEMARK,
            subject_type=SubjectType.INSTITUTION,
        )
        db_session.add(project)
        await db_session.commit()

        # 查询项目并验证关联
        result = await db_session.execute(
            select(Project).where(Project.owner_id == test_user.id)
        )
        projects = result.scalars().all()
        
        assert len(projects) == 1
        assert projects[0].name == "关系测试项目"

    async def test_project_metadata(self, db_session: AsyncSession, test_user: User):
        """测试项目元数据."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="元数据测试项目",
            project_type=ProjectType.COPYRIGHT,
            subject_type=SubjectType.ENTERPRISE,
            subject_name="测试企业",
            subject_id_number="91110000123456789X",
            development_method="independent",
            publication_status="unpublished",
            completion_date=date(2026, 1, 15),
            first_publication_date=date(2026, 2, 1),
            description="这是一个测试项目",
            tags=["软著", "测试", "Python"],
            meta_info={"key": "value", "count": 42},
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.subject_name == "测试企业"
        assert project.subject_id_number == "91110000123456789X"
        assert project.development_method == "independent"
        assert project.publication_status == "unpublished"
        assert project.completion_date == date(2026, 1, 15)
        assert project.first_publication_date == date(2026, 2, 1)
        assert project.description == "这是一个测试项目"
        assert project.tags == ["软著", "测试", "Python"]
        assert project.meta_info == {"key": "value", "count": 42}

    async def test_project_status_transitions(self, db_session: AsyncSession, test_user: User):
        """测试项目状态变更."""
        project = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="状态测试项目",
            project_type=ProjectType.COPYRIGHT,
            status=ProjectStatus.DRAFT,
            subject_type=SubjectType.INDIVIDUAL,
        )
        db_session.add(project)
        await db_session.commit()

        # 更新状态
        project.status = ProjectStatus.IN_PROGRESS
        project.current_step = 2
        await db_session.commit()
        await db_session.refresh(project)

        assert project.status == ProjectStatus.IN_PROGRESS
        assert project.current_step == 2
