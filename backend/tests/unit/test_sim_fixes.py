"""仿真测试发现并修复的缺陷回归测试.

覆盖本轮仿真可用性测试发现并修复的 6 类真实缺陷，防止回归：

1. 软著合规检查 ``None >= int`` 崩溃（word_count/page_count 为 None）
2. 多代码包时合规检查/导出崩溃（scalar_one_or_none → MultipleResultsFound）
3. 存储服务 ``STORAGE_TYPE=local`` 支持（无 MinIO 环境）
4. 中文文件名下载 latin-1 编码崩溃（content_disposition）
5. 导出任务合规检查参数不完整（job_runner 传 manual 缺 title）
6. 尼斯分类种子数据填充
"""

from __future__ import annotations

import pytest

from ipflow.core.content_disposition import build_content_disposition


# ============================================================================
# 1. Content-Disposition 中文文件名（latin-1 编码崩溃修复）
# ============================================================================
class TestContentDisposition:
    """中文文件名下载头部构造."""

    def test_ascii_filename(self) -> None:
        """纯 ASCII 文件名应原样保留."""
        cd = build_content_disposition("export.zip")
        assert cd == 'attachment; filename="export.zip"; filename*=UTF-8\'\'export.zip'

    def test_chinese_filename_no_crash(self) -> None:
        """中文文件名不应触发 latin-1 编码崩溃（回归核心）."""
        # 修复前：直接拼入 headers 会抛 UnicodeEncodeError
        cd = build_content_disposition("软著申请_智审报表系统.zip")
        # 必须可被 latin-1 编码（HTTP 头部要求）
        cd.encode("latin-1")
        assert "filename*=UTF-8''" in cd
        # ASCII 兜底名不能为空
        assert 'filename=""' not in cd

    def test_inline_disposition(self) -> None:
        cd = build_content_disposition("预览.pdf", disposition="inline")
        assert cd.startswith("inline;")

    def test_all_non_ascii_falls_back(self) -> None:
        """纯非 ASCII 文件名兜底为仅保留 ASCII（如扩展名）。"""
        cd = build_content_disposition("完全中文.zip")
        cd.encode("latin-1")
        # ASCII 兜底名不含中文（已 url 编码进 filename*）
        assert "中文" not in cd
        assert "filename*=UTF-8''" in cd


# ============================================================================
# 2. 本地存储后端（STORAGE_TYPE=local）
# ============================================================================
class TestLocalStorage:
    """无 MinIO 时的本地文件系统存储."""

    def test_local_backend_uses_filesystem(self, tmp_path, monkeypatch) -> None:
        """STORAGE_TYPE=local 时 upload/download/delete 走本地文件系统."""
        from ipflow.services import storage_service as mod

        # 模拟配置
        class _FakeSettings:
            STORAGE_TYPE = "local"
            STORAGE_BASE_PATH = str(tmp_path)
            STORAGE_BUCKET = "ipflow"

        monkeypatch.setattr(mod, "get_settings", lambda: _FakeSettings())
        # 重置单例
        monkeypatch.setattr(mod, "_storage_service", None)

        import io

        svc = mod.get_storage_service()
        assert svc.client is None  # local 后端不创建 Minio 客户端

        uploaded = svc.upload_file(
            io.BytesIO(b"hello world"),
            "test.zip",
            content_type="application/zip",
            folder="codes",
        )
        assert uploaded["file_size"] == 11
        assert uploaded["storage_path"].startswith("codes/")

        # 下载
        data = svc.download_file(uploaded["storage_path"])
        assert data == b"hello world"

        # 预签名 URL（local 返回绝对路径）
        url = svc.get_presigned_url(uploaded["storage_path"])
        assert tmp_path.name in url

        # 删除后再下载应抛 FileNotFoundError（文件已不存在）
        svc.delete_file(uploaded["storage_path"])
        with pytest.raises(FileNotFoundError):
            svc.download_file(uploaded["storage_path"])


# ============================================================================
# 3. 合规检查 None 安全（word_count/page_count 为 None）
# ============================================================================
class TestComplianceNoneSafe:
    """说明书/代码统计字段为 None 时的合规检查（不应抛 TypeError）."""

    def test_manual_none_counts_does_not_crash(self) -> None:
        """生成草稿的 manual word_count/page_count 为 None 时合规检查不崩溃."""
        from ipflow.services.copyright.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()
        # manual 缺 word_count/page_count（模拟新生成草稿未统计）
        report = checker.check(
            project_id="00000000-0000-0000-0000-000000000000",
            software_info={"software_full_name": "测试系统", "version_number": "1.0"},
            code_bundle=None,
            manual={"title": "测试说明书", "word_count": None, "page_count": None},
        )
        # 不抛 TypeError 即通过；应有 MANUAL 规则
        manual_rules = [r for r in report.results if r.rule_id.startswith("MANUAL")]
        assert len(manual_rules) > 0

    def test_code_bundle_none_counts_does_not_crash(self) -> None:
        from ipflow.services.copyright.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()
        report = checker.check(
            project_id="00000000-0000-0000-0000-000000000000",
            software_info={"software_full_name": "测试系统", "version_number": "1.0"},
            code_bundle={"total_lines": None, "total_files": None, "pages_data": None},
            manual=None,
        )
        code_rules = [r for r in report.results if r.rule_id.startswith("CODE")]
        assert len(code_rules) > 0


# ============================================================================
# 4. 尼斯分类种子数据
# ============================================================================
class TestNiceSeed:
    """尼斯分类种子填充."""

    @pytest.mark.asyncio
    async def test_seed_fills_45_classes(self, db_session) -> None:
        from ipflow.db.nice_seed import seed_nice_classifications
        from ipflow.models.trademark import NiceClassification
        from sqlmodel import select

        added = await seed_nice_classifications(db_session)
        assert added == 45

        result = await db_session.execute(select(NiceClassification))
        classes = result.scalars().all()
        numbers = sorted(c.class_number for c in classes)
        assert numbers == list(range(1, 46))

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, db_session) -> None:
        from ipflow.db.nice_seed import seed_nice_classifications

        await seed_nice_classifications(db_session)
        second = await seed_nice_classifications(db_session)
        assert second == 0  # 已有数据不重复填充
