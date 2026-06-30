"""代码处理引擎.

提供 ZIP 文件解压、代码文件识别、分页处理等功能。
"""

import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, BinaryIO


@dataclass
class CodeFileInfo:
    """代码文件信息."""
    
    path: str
    relative_path: str
    size: int
    lines: int
    language: str
    extension: str
    content: Optional[str] = None


@dataclass
class LanguageStats:
    """语言统计信息."""
    
    total_files: int
    total_lines: int
    languages: Dict[str, int] = field(default_factory=dict)


@dataclass
class PagedContent:
    """分页内容."""
    
    page_number: int
    content: str
    line_start: int
    line_end: int
    section: str  # "front" 或 "back"
    source_files: List[str] = field(default_factory=list)


class CodeProcessor:
    """代码处理器.
    
    处理软著代码材料的 ZIP 文件，包括：
    - ZIP 解压
    - 代码文件识别（支持 40+ 语言）
    - 目录过滤（node_modules, .git 等）
    - 行数统计与语言分析
    - 前30页+后30页分页
    - 行号添加与页眉生成
    """
    
    # 支持的代码文件扩展名
    CODE_EXTENSIONS: Set[str] = {
        # Python
        ".py", ".pyx", ".pyi", ".pyd",
        # JavaScript/TypeScript
        ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        # Java
        ".java", ".kt", ".scala", ".groovy",
        # C/C++
        ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx",
        # C#
        ".cs", ".csx",
        # Go
        ".go",
        # Rust
        ".rs", ".rlib",
        # Ruby
        ".rb", ".erb",
        # PHP
        ".php", ".phtml",
        # Swift
        ".swift",
        # Objective-C
        ".m", ".mm",
        # Web
        ".html", ".htm", ".css", ".scss", ".sass", ".less",
        ".vue", ".svelte",
        # Shell
        ".sh", ".bash", ".zsh", ".fish", ".ps1",
        # Config/Data
        ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        # SQL
        ".sql",
        # R
        ".r", ".R",
        # MATLAB
        ".m", ".matlab",
        # Perl
        ".pl", ".pm",
        # Lua
        ".lua",
        # Dart
        ".dart",
        # Flutter
        ".flutter",
        # Julia
        ".jl",
        # Haskell
        ".hs", ".lhs",
        # Lisp/Clojure
        ".clj", ".cljs", ".cljc", ".lisp", ".lsp",
        # Erlang/Elixir
        ".erl", ".ex", ".exs",
        # Other
        ".asm", ".s", ".v", ".sv", ".vhdl", ".verilog",
    }
    
    # 忽略的目录
    IGNORED_DIRS: Set[str] = {
        "node_modules",
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        "target",
        ".idea",
        ".vscode",
        "vendor",
        "third_party",
        "thirdparty",
        "lib",
        "libs",
        "bin",
        "obj",
        ".next",
        ".nuxt",
        "out",
        "public",
        "assets",
        "static",
        "uploads",
        "media",
        "coverage",
        ".coverage",
        "htmlcov",
        ".gradle",
        ".DS_Store",
    }
    
    # 忽略的文件
    IGNORED_FILES: Set[str] = {
        ".gitignore",
        ".gitattributes",
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
        "poetry.lock",
        "Pipfile.lock",
    }
    
    # 语言映射
    LANGUAGE_MAP: Dict[str, str] = {
        ".py": "python",
        ".pyx": "python",
        ".pyi": "python",
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".java": "java",
        ".kt": "kotlin",
        ".scala": "scala",
        ".groovy": "groovy",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".hxx": "cpp",
        ".cs": "csharp",
        ".csx": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rlib": "rust",
        ".rb": "ruby",
        ".erb": "ruby",
        ".php": "php",
        ".phtml": "php",
        ".swift": "swift",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".vue": "vue",
        ".svelte": "svelte",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".fish": "shell",
        ".ps1": "powershell",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "config",
        ".sql": "sql",
        ".r": "r",
        ".R": "r",
        ".lua": "lua",
        ".dart": "dart",
        ".jl": "julia",
        ".hs": "haskell",
        ".clj": "clojure",
        ".erl": "erlang",
        ".ex": "elixir",
        ".exs": "elixir",
        ".pl": "perl",
        ".pm": "perl",
    }
    
    def __init__(self, lines_per_page: int = 50):
        """初始化代码处理器.
        
        Args:
            lines_per_page: 每页代码行数，默认为 50
        """
        self.lines_per_page = lines_per_page
    
    def extract_zip(
        self, 
        zip_file: BinaryIO, 
        extract_path: Path,
    ) -> Path:
        """解压 ZIP 文件.
        
        Args:
            zip_file: ZIP 文件对象
            extract_path: 解压目标路径
            
        Returns:
            解压后的目录路径
        """
        extract_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(extract_path)
        
        return extract_path
    
    def is_code_file(self, file_path: str) -> bool:
        """检查是否为代码文件.
        
        根据扩展名和路径判断。
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为代码文件
        """
        path = Path(file_path)
        
        # 检查是否在忽略的目录中
        for parent in path.parents:
            if parent.name in self.IGNORED_DIRS:
                return False
        
        # 检查文件名是否在忽略列表中
        if path.name in self.IGNORED_FILES:
            return False
        
        # 检查扩展名
        ext = path.suffix.lower()
        return ext in self.CODE_EXTENSIONS
    
    def get_language(self, extension: str) -> str:
        """根据扩展名获取语言.
        
        Args:
            extension: 文件扩展名（包含点，如 .py）
            
        Returns:
            语言名称
        """
        return self.LANGUAGE_MAP.get(extension.lower(), "unknown")
    
    def scan_directory(self, directory: Path) -> List[CodeFileInfo]:
        """扫描目录获取代码文件.
        
        Args:
            directory: 要扫描的目录
            
        Returns:
            代码文件信息列表
        """
        code_files: List[CodeFileInfo] = []
        
        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue
            
            relative_path = file_path.relative_to(directory)
            
            if not self.is_code_file(str(relative_path)):
                continue
            
            # 尝试读取文件内容
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = self.count_lines(content)
                
                code_files.append(CodeFileInfo(
                    path=str(relative_path),
                    relative_path=str(relative_path),
                    size=file_path.stat().st_size,
                    lines=lines,
                    language=self.get_language(file_path.suffix),
                    extension=file_path.suffix.lower(),
                    content=content,
                ))
            except (IOError, OSError):
                # 无法读取的文件跳过
                continue
        
        # 按路径排序
        code_files.sort(key=lambda x: x.path)
        return code_files
    
    def count_lines(self, content: str) -> int:
        """统计内容行数.
        
        Args:
            content: 文件内容
            
        Returns:
            行数
        """
        if not content:
            return 0
        # 如果内容以换行符结尾，最后一行不应计数（空行）
        if content.endswith('\n'):
            content = content[:-1]
        return content.count('\n') + 1 if content else 0
    
    def calculate_language_stats(self, code_files: List[CodeFileInfo]) -> LanguageStats:
        """计算语言统计.
        
        Args:
            code_files: 代码文件列表
            
        Returns:
            语言统计信息
        """
        languages: Dict[str, int] = {}
        total_lines = 0
        
        for file in code_files:
            ext = file.extension
            languages[ext] = languages.get(ext, 0) + file.lines
            total_lines += file.lines
        
        return LanguageStats(
            total_files=len(code_files),
            total_lines=total_lines,
            languages=languages,
        )
    
    def merge_code_files(self, code_files: List[CodeFileInfo]) -> str:
        """合并代码文件.
        
        按照文件路径顺序合并所有代码文件，添加文件分隔注释。
        
        Args:
            code_files: 代码文件列表
            
        Returns:
            合并后的代码内容
        """
        merged_parts: List[str] = []
        
        for file in code_files:
            # 添加文件分隔注释
            separator = f"\n// ==================== File: {file.path} ====================\n"
            merged_parts.append(separator)

            if file.content:
                merged_parts.append(file.content)
                # 确保文件末尾有换行
                if not file.content.endswith('\n'):
                    merged_parts.append('\n')
        
        return ''.join(merged_parts)
    
    def paginate_code_front_back_30(
        self, 
        content: str,
        total_pages: int = 60,
        front_pages: int = 30,
    ) -> List[PagedContent]:
        """前30页+后30页分页.
        
        软著要求：前30页 + 后30页，共60页。
        如果代码不足3000行，则全部使用。
        
        Args:
            content: 合并后的代码内容
            total_pages: 总页数（默认60）
            front_pages: 前部分页数（默认30）
            
        Returns:
            分页内容列表
        """
        lines = content.split('\n')
        total_lines = len(lines)
        
        pages: List[PagedContent] = []
        
        # 如果代码不足 3000 行（60页 * 50行），则全部使用
        if total_lines <= total_pages * self.lines_per_page:
            # 全部归为 front section
            for page_num in range(0, (total_lines + self.lines_per_page - 1) // self.lines_per_page):
                start_line = page_num * self.lines_per_page + 1
                end_line = min((page_num + 1) * self.lines_per_page, total_lines)
                page_content = '\n'.join(lines[start_line - 1:end_line])
                
                pages.append(PagedContent(
                    page_number=page_num + 1,
                    content=page_content,
                    line_start=start_line,
                    line_end=end_line,
                    section="front",
                ))
        else:
            # 前30页
            for page_num in range(front_pages):
                start_line = page_num * self.lines_per_page + 1
                end_line = (page_num + 1) * self.lines_per_page
                page_content = '\n'.join(lines[start_line - 1:end_line])
                
                pages.append(PagedContent(
                    page_number=page_num + 1,
                    content=page_content,
                    line_start=start_line,
                    line_end=end_line,
                    section="front",
                ))
            
            # 后30页
            back_start_line = total_lines - (total_pages - front_pages) * self.lines_per_page + 1
            for page_num in range(total_pages - front_pages):
                start_line = back_start_line + page_num * self.lines_per_page
                end_line = min(back_start_line + (page_num + 1) * self.lines_per_page - 1, total_lines)
                page_content = '\n'.join(lines[start_line - 1:end_line])
                
                pages.append(PagedContent(
                    page_number=front_pages + page_num + 1,
                    content=page_content,
                    line_start=start_line,
                    line_end=end_line,
                    section="back",
                ))
        
        return pages
    
    def add_line_numbers(self, content: str, start_line: int = 1) -> str:
        """添加行号.
        
        格式：5位数字 + 4空格 + 代码
        
        Args:
            content: 代码内容
            start_line: 起始行号
            
        Returns:
            添加行号后的内容
        """
        lines = content.split('\n')
        numbered_lines: List[str] = []
        
        for i, line in enumerate(lines):
            line_num = start_line + i
            numbered_lines.append(f"{line_num:05d}    {line}")
        
        return '\n'.join(numbered_lines)
    
    def add_page_header(
        self, 
        content: str, 
        software_name: str, 
        version: str, 
        page_num: int,
    ) -> str:
        """添加页眉.
        
        格式：软件名称 V版本号 第X页
        
        Args:
            content: 页面内容
            software_name: 软件名称
            version: 版本号
            page_num: 页码
            
        Returns:
            添加页眉后的内容
        """
        header = f"{software_name} {version} 第{page_num}页"
        return f"{header}\n\n{content}"
    
    def process_zip_file(
        self,
        zip_file: BinaryIO,
        extract_dir: Path,
        software_name: str,
        version: str,
    ) -> dict:
        """处理 ZIP 文件的完整流程.
        
        Args:
            zip_file: ZIP 文件对象
            extract_dir: 解压目录
            software_name: 软件名称
            version: 版本号
            
        Returns:
            处理结果字典
        """
        # 解压
        extract_path = self.extract_zip(zip_file, extract_dir)
        
        # 扫描代码文件
        code_files = self.scan_directory(extract_path)
        
        # 计算统计
        stats = self.calculate_language_stats(code_files)
        
        # 合并代码
        merged_content = self.merge_code_files(code_files)
        
        # 分页
        pages = self.paginate_code_front_back_30(merged_content)
        
        # 检查是否有足够代码（3000行以上）
        has_enough_code = stats.total_lines >= 3000
        
        # 生成警告
        warnings: List[str] = []
        if not has_enough_code:
            warnings.append(f"代码总行数不足3000行（当前{stats.total_lines}行），建议补充更多代码")
        
        # 生成带行号和页眉的页面
        processed_pages = []
        for page in pages:
            numbered_content = self.add_line_numbers(page.content, page.line_start)
            final_content = self.add_page_header(
                numbered_content, software_name, version, page.page_number
            )
            processed_pages.append({
                "page_number": page.page_number,
                "content": final_content,
                "line_start": page.line_start,
                "line_end": page.line_end,
                "section": page.section,
            })
        
        return {
            "total_files": stats.total_files,
            "total_lines": stats.total_lines,
            "processed_lines": sum(p["line_end"] - p["line_start"] + 1 for p in processed_pages),
            "language_stats": stats.languages,
            "pages": processed_pages,
            "has_enough_code": has_enough_code,
            "warnings": warnings,
            "extract_path": str(extract_path),
        }
