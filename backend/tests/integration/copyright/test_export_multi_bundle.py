"""软著导出多代码包/多说明书查询回归测试.

覆盖蓝色审计指出的 ``export.py`` 缺陷：当某个 copyright_data 下存在
多条 ``CodeBundle`` 或多条 ``CopyrightManual`` 时，旧写法
``select(X).where(...)`` + ``scalar_one_or_none()`` 会抛
``MultipleResultsFound`` 导致导出崩溃；修复后写法
``.order_by(X.created_at.desc())`` + ``scalars().first()`` 应返回最新一条。

本文件断言两种写法的行为差异，防止回归。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.exc import MultipleResultsFound
from sqlmodel import select

from ipflow.models import CodeBundle, CopyrightData, CopyrightManual, Project
from ipflow.models.enums import SubjectType
from ipflow.models.project import ProjectType


async def _seed_copyright_with_bundles(db_session) -> tuple[CopyrightData, CodeBundle, CodeBundle]:
    """构造 1 Project + 1 CopyrightData + 2 CodeBundle（第二条较新）.

    Returns:
        (copyright_data, older_bundle, newer_bundle)
    """
    owner_id = uuid4()

    project = Project(
        id=uuid4(),
        owner_id=owner_id,
        project_type=ProjectType.COPYRIGHT,
        name="多代码包回归测试项目",
        subject_type=SubjectType.INDIVIDUAL,
    )
    db_session.add(project)
    await db_session.flush()

    copyright_data = CopyrightData(
        id=uuid4(),
        project_id=project.id,
        software_full_name="回归测试系统",
        version_number="1.0",
        development_language="Python",
    )
    db_session.add(copyright_data)
    await db_session.flush()

    base = datetime(2025, 1, 1, 12, 0, 0)

    older_bundle = CodeBundle(
        id=uuid4(),
        copyright_data_id=copyright_data.id,
        original_file_name="old.zip",
        original_file_size=100,
        total_files=1,
        total_lines=10,
        processed_lines=8,
        created_at=base,
        updated_at=base,
    )
    newer_bundle = CodeBundle(
        id=uuid4(),
        copyright_data_id=copyright_data.id,
        original_file_name="new.zip",
        original_file_size=200,
        total_files=2,
        total_lines=20,
        processed_lines=18,
        created_at=base + timedelta(days=1),
        updated_at=base + timedelta(days=1),
    )
    db_session.add_all([older_bundle, newer_bundle])
    await db_session.commit()
    await db_session.refresh(older_bundle)
    await db_session.refresh(newer_bundle)

    return copyright_data, older_bundle, newer_bundle


@pytest.mark.asyncio
async def test_code_bundle_query_returns_latest_not_crash(db_session) -> None:
    """多个 CodeBundle：旧写法抛 MultipleResultsFound，新写法返回最新一条."""
    copyright_data, older_bundle, newer_bundle = await _seed_copyright_with_bundles(db_session)

    # ---- 旧写法（export.py 修复前）：多行 → MultipleResultsFound ----
    old_stmt = select(CodeBundle).where(
        CodeBundle.copyright_data_id == copyright_data.id
    )
    old_result = await db_session.execute(old_stmt)
    with pytest.raises(MultipleResultsFound):
        old_result.scalar_one_or_none()

    # ---- 新写法（export.py 修复后）：order_by + scalars().first() ----
    new_stmt = (
        select(CodeBundle)
        .where(CodeBundle.copyright_data_id == copyright_data.id)
        .order_by(CodeBundle.created_at.desc())
    )
    new_result = await db_session.execute(new_stmt)
    latest = new_result.scalars().first()

    assert latest is not None
    assert latest.id == newer_bundle.id
    assert latest.created_at == newer_bundle.created_at
    assert latest.created_at > older_bundle.created_at


@pytest.mark.asyncio
async def test_manual_query_returns_latest_not_crash(db_session) -> None:
    """多个 CopyrightManual：旧写法抛 MultipleResultsFound，新写法返回最新一条."""
    owner_id = uuid4()
    project = Project(
        id=uuid4(),
        owner_id=owner_id,
        project_type=ProjectType.COPYRIGHT,
        name="多说明书回归测试项目",
        subject_type=SubjectType.INDIVIDUAL,
    )
    db_session.add(project)
    await db_session.flush()

    copyright_data = CopyrightData(
        id=uuid4(),
        project_id=project.id,
        software_full_name="回归测试系统",
        version_number="1.0",
        development_language="Python",
    )
    db_session.add(copyright_data)
    await db_session.flush()

    base = datetime(2025, 1, 1, 12, 0, 0)
    older_manual = CopyrightManual(
        id=uuid4(),
        copyright_data_id=copyright_data.id,
        template_type="web",
        title="旧说明书",
        created_at=base,
        updated_at=base,
    )
    newer_manual = CopyrightManual(
        id=uuid4(),
        copyright_data_id=copyright_data.id,
        template_type="web",
        title="新说明书",
        created_at=base + timedelta(days=1),
        updated_at=base + timedelta(days=1),
    )
    db_session.add_all([older_manual, newer_manual])
    await db_session.commit()
    await db_session.refresh(older_manual)
    await db_session.refresh(newer_manual)

    # ---- 旧写法（export.py 修复前）：多行 → MultipleResultsFound ----
    old_stmt = select(CopyrightManual).where(
        CopyrightManual.copyright_data_id == copyright_data.id
    )
    old_result = await db_session.execute(old_stmt)
    with pytest.raises(MultipleResultsFound):
        old_result.scalar_one_or_none()

    # ---- 新写法（export.py 修复后）：order_by + scalars().first() ----
    new_stmt = (
        select(CopyrightManual)
        .where(CopyrightManual.copyright_data_id == copyright_data.id)
        .order_by(CopyrightManual.created_at.desc())
    )
    new_result = await db_session.execute(new_stmt)
    latest = new_result.scalars().first()

    assert latest is not None
    assert latest.id == newer_manual.id
    assert latest.created_at == newer_manual.created_at
    assert latest.created_at > older_manual.created_at
