"""代码处理服务测试.

测试 ZIP 文件处理、代码文件识别、分页引擎等功能。
"""

import io
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ipflow.services.copyright.code_processor import (
    CodeProcessor,
    CodeFileInfo,
    LanguageStats,
    PagedContent,
)


class TestCodeFileInfo:
    """测试代码文件信息模型."""

    def test_code_file_info_creation(self):
        """测试创建代码文件信息对象."""
        info = CodeFileInfo(
            path="src/main.py",
            relative_path="src/main.py",
            size=1024,
            lines=50,
            language="python",
            extension=".py",
        )
        assert info.path == "src/main.py"
        assert info.lines == 50
        assert info.language == "python"


class TestLanguageStats:
    """测试语言统计模型."""

    def test_language_stats_creation(self):
        """测试创建语言统计对象."""
        stats = LanguageStats(
            total_files=10,
            total_lines=1000,
            languages={".py": 500, ".js": 300, ".ts": 200},
        )
        assert stats.total_files == 10
        assert stats.total_lines == 1000
        assert stats.languages[".py"] == 500


class TestPagedContent:
    """测试分页内容模型."""

    def test_paged_content_creation(self):
        """测试创建分页内容对象."""
        page = PagedContent(
            page_number=1,
            content="print('hello')",
            line_start=1,
            line_end=1,
            section="front",
            source_files=["main.py"],
        )
        assert page.page_number == 1
        assert page.section == "front"
        assert page.line_start == 1


class TestCodeProcessor:
    """测试代码处理器."""

    @pytest.fixture
    def processor(self):
        """创建代码处理器实例."""
        return CodeProcessor()

    @pytest.fixture
    def sample_zip(self):
        """创建包含示例代码文件的 ZIP 文件."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Python 文件
            zf.writestr("main.py", "# Main entry\\nprint('hello')\\n")
            zf.writestr("utils.py", "# Utilities\\ndef helper():\\n    pass\\n")
            
            # JavaScript 文件
            zf.writestr("app.js", "// App\\nconsole.log('app');\\n")
            
            # 应该被忽略的文件
            zf.writestr("node_modules/lib.js", "// lib\\n")
            zf.writestr(".git/config", "[core]")
            zf.writestr("__pycache__/cache.pyc", "cached")
            
            # 非代码文件
            zf.writestr("README.md", "# README")
            zf.writestr("data.json", '{"key": "value"}')
        
        zip_buffer.seek(0)
        return zip_buffer

    def test_extract_zip(self, processor, sample_zip):
        """测试解压 ZIP 文件."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extracted"
            
            result = processor.extract_zip(sample_zip, extract_path)
            
            assert result == extract_path
            assert (extract_path / "main.py").exists()
            assert (extract_path / "utils.py").exists()
            # 应该解压所有文件
            assert (extract_path / "node_modules" / "lib.js").exists()

    def test_is_code_file(self, processor):
        """测试代码文件识别."""
        # 代码文件
        assert processor.is_code_file("main.py") is True
        assert processor.is_code_file("app.js") is True
        assert processor.is_code_file("main.java") is True
        assert processor.is_code_file("program.c") is True
        assert processor.is_code_file("script.cpp") is True
        assert processor.is_code_file("lib.rs") is True
        assert processor.is_code_file("app.go") is True
        assert processor.is_code_file("Main.kt") is True
        assert processor.is_code_file("app.ts") is True
        assert processor.is_code_file("style.scss") is True
        
        # 非代码文件
        assert processor.is_code_file("README.md") is False
        assert processor.is_code_file("data.json") is False
        assert processor.is_code_file("image.png") is False
        assert processor.is_code_file("doc.pdf") is False
        
        # 忽略的目录
        assert processor.is_code_file("node_modules/lib.js") is False
        assert processor.is_code_file(".git/config") is False
        assert processor.is_code_file("__pycache__/cache.py") is False
        assert processor.is_code_file("dist/bundle.js") is False

    def test_get_language_by_extension(self, processor):
        """测试根据扩展名获取语言."""
        assert processor.get_language(".py") == "python"
        assert processor.get_language(".js") == "javascript"
        assert processor.get_language(".ts") == "typescript"
        assert processor.get_language(".java") == "java"
        assert processor.get_language(".cpp") == "cpp"
        assert processor.get_language(".c") == "c"
        assert processor.get_language(".go") == "go"
        assert processor.get_language(".rs") == "rust"
        assert processor.get_language(".vue") == "vue"
        assert processor.get_language(".jsx") == "jsx"
        assert processor.get_language(".tsx") == "tsx"
        assert processor.get_language(".unknown") == "unknown"

    def test_scan_directory(self, processor, sample_zip):
        """测试扫描目录获取代码文件."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extracted"
            processor.extract_zip(sample_zip, extract_path)
            
            code_files = processor.scan_directory(extract_path)
            
            # 应该只返回代码文件（过滤掉 node_modules, .git, __pycache__）
            file_paths = [f.path for f in code_files]
            assert "main.py" in file_paths
            assert "utils.py" in file_paths
            assert "app.js" in file_paths
            assert "node_modules/lib.js" not in file_paths
            assert ".git/config" not in file_paths

    def test_count_lines(self, processor):
        """测试行数统计."""
        content = "line1\nline2\nline3\n"
        assert processor.count_lines(content) == 3
        
        # 空内容
        assert processor.count_lines("") == 0
        
        # 单行无换行
        assert processor.count_lines("single line") == 1

    def test_calculate_language_stats(self, processor, sample_zip):
        """测试语言统计计算."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extracted"
            processor.extract_zip(sample_zip, extract_path)
            code_files = processor.scan_directory(extract_path)
            
            stats = processor.calculate_language_stats(code_files)
            
            assert stats.total_files >= 3  # main.py, utils.py, app.js
            assert ".py" in stats.languages
            assert ".js" in stats.languages

    def test_merge_code_files(self, processor):
        """测试合并代码文件."""
        code_files = [
            CodeFileInfo(
                path="a.py",
                relative_path="a.py",
                size=100,
                lines=2,
                language="python",
                extension=".py",
                content="# File A\nprint('a')",
            ),
            CodeFileInfo(
                path="b.py",
                relative_path="b.py",
                size=100,
                lines=2,
                language="python",
                extension=".py",
                content="# File B\nprint('b')",
            ),
        ]
        
        merged = processor.merge_code_files(code_files)

        assert "# File A" in merged
        assert "# File B" in merged
        assert "print('a')" in merged
        assert "print('b')" in merged

    def test_merge_code_files_uses_real_newlines(self, processor):
        """回归测试：合并代码必须使用真实换行（0x0a），不得转义为字面 ``\\n``.

        上线前测试缺陷 #3：``merge_code_files`` 的文件分隔符曾误用 ``f"\\\\n//..."``，
        导致导出源代码全部塌成单行，破坏软著「每页50行带行号」规范。
        """
        code_files = [
            CodeFileInfo(
                path="a.py",
                relative_path="a.py",
                size=10,
                lines=1,
                language="python",
                extension=".py",
                content="print('a')",
            ),
        ]
        merged = processor.merge_code_files(code_files)
        # 必须含真实换行，且不得含字面的反斜杠+n 两字节序列
        assert "\n" in merged
        assert "\\n" not in merged
        # 文件分隔注释应是真实换行包裹，而非字面 \n
        assert "\n// ==================== File: a.py" in merged

    def test_paginate_code_front_back_30(self, processor):
        """测试前30页+后30页分页."""
        # 生成 100 页的内容（每页 50 行）
        lines = []
        for i in range(1, 5001):
            lines.append(f"Line {i:04d}: This is line content")
        content = "\n".join(lines)
        
        pages = processor.paginate_code_front_back_30(content)
        
        # 应该有 60 页（前30 + 后30）
        assert len(pages) == 60
        
        # 第一页
        assert pages[0].page_number == 1
        assert pages[0].section == "front"
        assert pages[0].line_start == 1
        assert pages[0].line_end == 50
        
        # 第30页（前部分最后一页）
        assert pages[29].page_number == 30
        assert pages[29].section == "front"
        assert pages[29].line_end == 1500
        
        # 第31页（后部分第一页）
        assert pages[30].page_number == 31
        assert pages[30].section == "back"
        
        # 最后一页
        assert pages[59].page_number == 60
        assert pages[59].section == "back"
        assert pages[59].line_end == 5000

    def test_paginate_code_insufficient_lines(self, processor):
        """测试代码不足3000行的处理."""
        # 只有 100 行（不足3000行，应该全部使用）
        lines = [f"Line {i}" for i in range(1, 101)]
        content = "\n".join(lines)
        
        pages = processor.paginate_code_front_back_30(content)

        # 应该只有 2 页（100行 / 50行每页）
        assert len(pages) == 2
        assert pages[0].section == "front"
        assert pages[1].section == "front"  # 不足时全部归为 front

    def test_paginate_code_uses_real_newlines(self, processor):
        """回归测试：分页内容必须用真实换行连接，不得转义为字面 ``\\n``.

        上线前测试缺陷 #3：``paginate_code_front_back_30`` 曾用 ``'\\\\n'.join(...)``
        连接页面行，导致导出源代码换行被字面化、无法按页50行打印。
        """
        lines = [f"Line {i}" for i in range(1, 121)]  # 120 行 → 3 页（不足3000，全 front）
        content = "\n".join(lines)

        pages = processor.paginate_code_front_back_30(content)
        assert len(pages) >= 2
        for page in pages:
            # 每页内容必须含真实换行（多行），且不含字面的反斜杠+n
            assert "\n" in page.content
            assert "\\n" not in page.content

    def test_add_line_numbers(self, processor):
        """测试添加行号."""
        content = "line1\nline2\nline3"
        numbered = processor.add_line_numbers(content, start_line=1)
        
        assert "00001    line1" in numbered
        assert "00002    line2" in numbered
        assert "00003    line3" in numbered

    def test_add_page_header(self, processor):
        """测试添加页眉."""
        content = "code content"
        software_name = "测试软件"
        version = "V1.0"
        page_num = 1
        
        header_content = processor.add_page_header(
            content, software_name, version, page_num
        )
        
        assert software_name in header_content
        assert version in header_content
        assert str(page_num) in header_content
        assert content in header_content

    def test_process_zip_file(self, processor, sample_zip):
        """测试完整的 ZIP 处理流程."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = processor.process_zip_file(
                zip_file=sample_zip,
                extract_dir=Path(temp_dir) / "extract",
                software_name="测试软件",
                version="V1.0",
            )
            
            # 验证结果结构
            assert "total_files" in result
            assert "total_lines" in result
            assert "processed_lines" in result
            assert "language_stats" in result
            assert "pages" in result
            assert "has_enough_code" in result
            
            # 验证统计
            assert result["total_files"] >= 3
            assert result["language_stats"][".py"] > 0
            assert result["language_stats"][".js"] > 0

    def test_process_zip_file_insufficient_code(self, processor):
        """测试代码不足的警告."""
        # 创建只有少量代码的 ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("small.py", "# small\\n")
        zip_buffer.seek(0)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = processor.process_zip_file(
                zip_file=zip_buffer,
                extract_dir=Path(temp_dir) / "extract",
                software_name="测试软件",
                version="V1.0",
            )
            
            assert result["has_enough_code"] is False
            assert len(result["warnings"]) > 0
            assert "3000行" in result["warnings"][0]


class TestCodeProcessorEdgeCases:
    """测试边界情况."""

    @pytest.fixture
    def processor(self):
        """创建代码处理器实例."""
        return CodeProcessor()

    def test_empty_zip(self, processor):
        """测试空 ZIP 文件."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            pass  # 空 ZIP
        zip_buffer.seek(0)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = processor.process_zip_file(
                zip_file=zip_buffer,
                extract_dir=Path(temp_dir) / "extract",
                software_name="测试软件",
                version="V1.0",
            )
            
            assert result["total_files"] == 0
            assert result["has_enough_code"] is False

    def test_binary_files_ignored(self, processor):
        """测试二进制文件被忽略."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("program.py", "print('hello')")
            zf.writestr("image.png", b"\\x89PNG\\r\\n\\x1a\\n")  # 二进制
            zf.writestr("data.db", b"\\x00\\x01\\x02\\x03")  # 二进制
        zip_buffer.seek(0)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            processor.extract_zip(zip_buffer, extract_path)
            code_files = processor.scan_directory(extract_path)
            
            file_paths = [f.path for f in code_files]
            assert "program.py" in file_paths
            assert "image.png" not in file_paths
            assert "data.db" not in file_paths

    def test_very_long_lines(self, processor):
        """测试超长行处理."""
        # 创建超过 80 字符的行
        long_line = "x" * 200
        content = f"line1\n{long_line}\nline3"
        
        # 应该正常处理，不进行截断
        numbered = processor.add_line_numbers(content, start_line=1)
        assert long_line in numbered
