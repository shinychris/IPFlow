"""用户模型单元测试.

测试 User 模型的创建、验证和枚举类型。
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlmodel import Field, SQLModel

from ipflow.models.user import User, UserRole, UserStatus


class TestUserRoleEnum:
    """测试用户角色枚举."""

    def test_user_role_values(self) -> None:
        """测试 UserRole 枚举值."""
        assert UserRole.SUPER_ADMIN == "super_admin"
        assert UserRole.ADMIN == "admin"
        assert UserRole.MANAGER == "manager"
        assert UserRole.MEMBER == "member"
        assert UserRole.VIEWER == "viewer"

    def test_user_role_is_str_enum(self) -> None:
        """测试 UserRole 是字符串枚举."""
        assert issubclass(UserRole, str)
        assert issubclass(UserRole, Enum)

    def test_user_role_from_string(self) -> None:
        """测试从字符串创建 UserRole."""
        assert UserRole("super_admin") == UserRole.SUPER_ADMIN
        assert UserRole("admin") == UserRole.ADMIN
        assert UserRole("member") == UserRole.MEMBER

    def test_invalid_user_role(self) -> None:
        """测试无效的 UserRole 值."""
        with pytest.raises(ValueError):
            UserRole("invalid_role")


class TestUserStatusEnum:
    """测试用户状态枚举."""

    def test_user_status_values(self) -> None:
        """测试 UserStatus 枚举值."""
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
        assert UserStatus.SUSPENDED == "suspended"
        assert UserStatus.PENDING == "pending"

    def test_user_status_is_str_enum(self) -> None:
        """测试 UserStatus 是字符串枚举."""
        assert issubclass(UserStatus, str)
        assert issubclass(UserStatus, Enum)

    def test_user_status_from_string(self) -> None:
        """测试从字符串创建 UserStatus."""
        assert UserStatus("active") == UserStatus.ACTIVE
        assert UserStatus("inactive") == UserStatus.INACTIVE
        assert UserStatus("pending") == UserStatus.PENDING

    def test_invalid_user_status(self) -> None:
        """测试无效的 UserStatus 值."""
        with pytest.raises(ValueError):
            UserStatus("invalid_status")


class TestUserModel:
    """测试 User 模型."""

    def test_user_model_is_table(self) -> None:
        """测试 User 是 SQLModel 表模型."""
        assert hasattr(User, "__tablename__")
        assert User.__tablename__ == "user"

    def test_user_model_inherits_sqlmodel(self) -> None:
        """测试 User 继承自 SQLModel."""
        assert issubclass(User, SQLModel)

    def test_user_basic_creation(self) -> None:
        """测试创建基本用户实例."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_string",
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password_string"
        assert user.id is not None
        assert isinstance(user.id, UUID)

    def test_user_default_values(self) -> None:
        """测试用户默认值."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_string",
        )
        
        # 默认角色应该是 member
        assert user.role == UserRole.MEMBER
        # 默认状态应该是 pending
        assert user.status == UserStatus.PENDING
        # 默认未验证
        assert user.is_verified is False
        # 可选字段默认为 None
        assert user.display_name is None
        assert user.avatar_url is None
        assert user.phone is None
        assert user.last_login_at is None

    def test_user_with_optional_fields(self) -> None:
        """测试带可选字段的用户创建."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_string",
            display_name="Test User",
            avatar_url="https://example.com/avatar.png",
            phone="+86 13800138000",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_verified=True,
        )
        
        assert user.display_name == "Test User"
        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.phone == "+86 13800138000"
        assert user.role == UserRole.ADMIN
        assert user.status == UserStatus.ACTIVE
        assert user.is_verified is True

    def test_user_with_role_enum(self) -> None:
        """测试使用枚举值设置角色."""
        user_admin = User(
            email="admin@example.com",
            username="adminuser",
            hashed_password="hash",
            role=UserRole.ADMIN,
        )
        assert user_admin.role == UserRole.ADMIN

        user_super = User(
            email="super@example.com",
            username="superuser",
            hashed_password="hash",
            role=UserRole.SUPER_ADMIN,
        )
        assert user_super.role == UserRole.SUPER_ADMIN

        user_manager = User(
            email="manager@example.com",
            username="manageruser",
            hashed_password="hash",
            role=UserRole.MANAGER,
        )
        assert user_manager.role == UserRole.MANAGER

        user_viewer = User(
            email="viewer@example.com",
            username="vieweruser",
            hashed_password="hash",
            role=UserRole.VIEWER,
        )
        assert user_viewer.role == UserRole.VIEWER

    def test_user_with_status_enum(self) -> None:
        """测试使用枚举值设置状态."""
        user_active = User(
            email="active@example.com",
            username="activeuser",
            hashed_password="hash",
            status=UserStatus.ACTIVE,
        )
        assert user_active.status == UserStatus.ACTIVE

        user_inactive = User(
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password="hash",
            status=UserStatus.INACTIVE,
        )
        assert user_inactive.status == UserStatus.INACTIVE

        user_suspended = User(
            email="suspended@example.com",
            username="suspendeduser",
            hashed_password="hash",
            status=UserStatus.SUSPENDED,
        )
        assert user_suspended.status == UserStatus.SUSPENDED

    def test_user_email_validation(self) -> None:
        """测试邮箱格式存储."""
        # SQLModel 表模型实例化时不自动验证，验证应在 Schema 层处理
        # 有效邮箱
        user = User(
            email="valid.email+tag@example.com",
            username="testuser1",
            hashed_password="hash",
        )
        assert user.email == "valid.email+tag@example.com"

        # SQLModel 表模型接受任意字符串作为 email
        # 实际验证应在 API Schema 或 Service 层进行
        user_invalid = User(
            email="invalid-email-string",
            username="testuser2",
            hashed_password="hash",
        )
        assert user_invalid.email == "invalid-email-string"

    def test_user_required_fields(self) -> None:
        """测试必填字段的默认值行为."""
        # SQLModel 表模型实例化时不会强制验证必填字段
        # 必填约束在数据库层面生效
        
        # 可以创建缺少字段的实例（但无法保存到数据库）
        user_no_email = User(
            username="testuser",
            hashed_password="hash",
        )
        assert user_no_email.email is None

        user_no_username = User(
            email="test@example.com",
            hashed_password="hash",
        )
        assert user_no_username.username is None

        user_no_password = User(
            email="test@example.com",
            username="testuser",
        )
        assert user_no_password.hashed_password is None

    def test_user_id_auto_generation(self) -> None:
        """测试 UUID 自动生成."""
        user1 = User(
            email="user1@example.com",
            username="user1",
            hashed_password="hash",
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            hashed_password="hash",
        )
        
        assert user1.id is not None
        assert user2.id is not None
        assert user1.id != user2.id
        assert isinstance(user1.id, UUID)
        assert isinstance(user2.id, UUID)

    def test_user_id_can_be_set(self) -> None:
        """测试可以手动设置 UUID."""
        custom_id = uuid4()
        user = User(
            id=custom_id,
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
        )
        assert user.id == custom_id

    def test_user_has_timestamp_fields(self) -> None:
        """测试 User 有时间戳字段."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
        )
        
        # 检查字段存在
        assert hasattr(user, "created_at")
        assert hasattr(user, "updated_at")

    def test_user_has_sa_columns(self) -> None:
        """测试 User 有正确的 SQLAlchemy 列配置."""
        # 检查表模型属性
        assert hasattr(User, "__table__")
        
        table = User.__table__
        
        # 检查列存在
        assert "id" in table.columns
        assert "email" in table.columns
        assert "username" in table.columns
        assert "hashed_password" in table.columns
        assert "display_name" in table.columns
        assert "avatar_url" in table.columns
        assert "phone" in table.columns
        assert "role" in table.columns
        assert "status" in table.columns
        assert "is_verified" in table.columns
        assert "last_login_at" in table.columns
        assert "created_at" in table.columns
        assert "updated_at" in table.columns

    def test_user_email_unique_index(self) -> None:
        """测试 email 字段有唯一索引."""
        table = User.__table__
        email_col = table.columns["email"]
        
        assert email_col.unique is True
        assert email_col.index is True

    def test_user_username_unique_index(self) -> None:
        """测试 username 字段有唯一索引."""
        table = User.__table__
        username_col = table.columns["username"]
        
        assert username_col.unique is True
        assert username_col.index is True

    def test_user_username_max_length(self) -> None:
        """测试 username 最大长度限制."""
        table = User.__table__
        username_col = table.columns["username"]
        
        assert username_col.type.length == 50

    def test_user_email_max_length(self) -> None:
        """测试 email 最大长度限制."""
        table = User.__table__
        email_col = table.columns["email"]
        
        assert email_col.type.length == 255

    def test_user_hashed_password_max_length(self) -> None:
        """测试 hashed_password 最大长度限制."""
        table = User.__table__
        password_col = table.columns["hashed_password"]
        
        assert password_col.type.length == 255

    def test_user_display_name_max_length(self) -> None:
        """测试 display_name 最大长度限制."""
        table = User.__table__
        display_name_col = table.columns["display_name"]
        
        assert display_name_col.type.length == 100

    def test_user_phone_max_length(self) -> None:
        """测试 phone 最大长度限制."""
        table = User.__table__
        phone_col = table.columns["phone"]
        
        assert phone_col.type.length == 20

    def test_user_last_login_at_nullable(self) -> None:
        """测试 last_login_at 可为空."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
        )
        assert user.last_login_at is None

    def test_user_timestamps_are_datetime(self) -> None:
        """测试时间戳字段类型为 datetime."""
        now = datetime.utcnow()
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            created_at=now,
            updated_at=now,
        )
        assert user.created_at == now
        assert user.updated_at == now
