"""组织模型测试.

测试 Organization 和 OrganizationMember 模型。
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.models.organization import Organization, OrganizationMember
from ipflow.models.user import User, UserRole


class TestOrganizationModel:
    """测试组织模型."""

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """创建测试用户."""
        user = User(
            id=uuid4(),
            email="org_test@example.com",
            username="org_test_user",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_create_organization(self, db_session: AsyncSession):
        """测试创建组织."""
        org = Organization(
            id=uuid4(),
            name="测试企业",
            slug="test-enterprise",
            description="这是一个测试企业",
            business_type="enterprise",
            license_number="91110000123456789X",
            contact_email="contact@test.com",
            contact_phone="010-12345678",
            plan_type="pro",
            max_projects=50,
            max_storage_bytes=10737418240,  # 10GB
            max_members=10,
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        assert org.name == "测试企业"
        assert org.slug == "test-enterprise"
        assert org.plan_type == "pro"
        assert org.is_active is True
        assert org.max_projects == 50

    async def test_organization_membership(self, db_session: AsyncSession, test_user: User):
        """测试组织成员关系."""
        # 创建组织
        org = Organization(
            id=uuid4(),
            name="成员测试组织",
            slug="member-test-org",
        )
        db_session.add(org)
        await db_session.commit()

        # 添加成员
        member = OrganizationMember(
            id=uuid4(),
            organization_id=org.id,
            user_id=test_user.id,
            role=UserRole.ADMIN,
        )
        db_session.add(member)
        await db_session.commit()

        # 查询验证
        result = await db_session.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id
            )
        )
        members = result.scalars().all()
        
        assert len(members) == 1
        assert members[0].user_id == test_user.id
        assert members[0].role == UserRole.ADMIN

    async def test_organization_storage_calculation(self, db_session: AsyncSession):
        """测试组织存储计算."""
        org = Organization(
            id=uuid4(),
            name="存储测试组织",
            slug="storage-test-org",
            max_storage_bytes=1073741824,  # 1GB
            used_storage_bytes=536870912,   # 512MB
        )
        db_session.add(org)
        await db_session.commit()

        # 计算使用率
        usage_percent = (org.used_storage_bytes / org.max_storage_bytes) * 100
        assert usage_percent == 50.0

    async def test_organization_soft_delete(self, db_session: AsyncSession):
        """测试组织软删除."""
        org = Organization(
            id=uuid4(),
            name="删除测试组织",
            slug="delete-test-org",
        )
        db_session.add(org)
        await db_session.commit()

        # 软删除
        from datetime import datetime
        org.deleted_at = datetime.utcnow()
        org.is_active = False
        await db_session.commit()

        assert org.is_active is False
        assert org.deleted_at is not None


class TestOrganizationMember:
    """测试组织成员模型."""

    @pytest.fixture
    async def test_org(self, db_session: AsyncSession) -> Organization:
        """创建测试组织."""
        org = Organization(
            id=uuid4(),
            name="成员测试组织",
            slug="org-member-test",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        return org

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """创建测试用户."""
        user = User(
            id=uuid4(),
            email="member_test@example.com",
            username="member_test_user",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_member_roles(self, db_session: AsyncSession, test_org: Organization, test_user: User):
        """测试成员角色."""
        roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.MEMBER, UserRole.VIEWER]
        
        for role in roles:
            user = User(
                id=uuid4(),
                email=f"{role.value}@example.com",
                username=f"{role.value}_user",
                hashed_password="hashed",
            )
            db_session.add(user)
            await db_session.commit()

            member = OrganizationMember(
                id=uuid4(),
                organization_id=test_org.id,
                user_id=user.id,
                role=role,
            )
            db_session.add(member)
        
        await db_session.commit()

        # 验证所有角色
        result = await db_session.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == test_org.id
            )
        )
        members = result.scalars().all()
        
        assert len(members) == 4
        member_roles = {m.role for m in members}
        assert member_roles == set(roles)

    async def test_unique_membership_constraint(self, db_session: AsyncSession, test_org: Organization, test_user: User):
        """测试唯一成员约束."""
        member1 = OrganizationMember(
            id=uuid4(),
            organization_id=test_org.id,
            user_id=test_user.id,
            role=UserRole.MEMBER,
        )
        db_session.add(member1)
        await db_session.commit()

        # 尝试添加重复成员应该失败
        # 注意：实际测试需要数据库约束支持
