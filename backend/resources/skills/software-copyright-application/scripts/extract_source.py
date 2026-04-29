#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软著源代码提取工具

从项目中提取符合中国版权保护中心格式要求的源代码文档。
支持自动生成前30页和后30页源代码。

使用方法:
    python extract_source.py --project-path /path/to/project \
        --software-name "XX管理系统" \
        --version "V1.0" \
        --output-dir ./output
"""

import os
import re
import argparse
from pathlib import Path
from datetime import datetime


# 默认支持的代码文件扩展名
DEFAULT_EXTENSIONS = {
    '.java', '.py', '.js', '.ts', '.jsx', '.tsx',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.go',
    '.php', '.rb', '.swift', '.kt', '.scala',
    '.vue', '.html', '.css', '.scss', '.less',
    '.sql', '.xml', '.json', '.yaml', '.yml',
    '.sh', '.bat', '.ps1', '.r', '.m', '.mm'
}

# 默认排除的目录
DEFAULT_EXCLUDE_DIRS = {
    '.git', '.svn', '.hg', 'node_modules', 'vendor',
    'target', 'build', 'dist', 'out', '.idea', '.vscode',
    '__pycache__', '.gradle', 'bin', 'obj', 'release',
    'debug', 'logs', 'temp', 'tmp', 'uploads', 'assets',
    'public', 'static', 'test', 'tests', 'spec', 'mock'
}

# 默认排除的文件
DEFAULT_EXCLUDE_FILES = {
    '.gitignore', '.gitattributes', '.editorconfig',
    '.dockerignore', 'LICENSE', 'README', 'CHANGELOG',
    'Makefile', 'CMakeLists.txt', 'package-lock.json',
    'yarn.lock', 'pnpm-lock.yaml', 'Cargo.lock',
    'requirements.txt', 'Gemfile.lock', 'composer.lock'
}


def get_all_code_files(project_path, extensions=None, exclude_dirs=None, exclude_files=None):
    """
    获取项目中所有代码文件
    
    Args:
        project_path: 项目根目录路径
        extensions: 包含的文件扩展名集合
        exclude_dirs: 排除的目录集合
        exclude_files: 排除的文件名集合
    
    Returns:
        list: 代码文件路径列表
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    if exclude_files is None:
        exclude_files = DEFAULT_EXCLUDE_FILES
    
    code_files = []
    project_path = Path(project_path).resolve()
    
    for root, dirs, files in os.walk(project_path):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            # 跳过隐藏文件
            if file.startswith('.'):
                continue
            # 跳过排除的文件
            if file in exclude_files:
                continue
            # 检查扩展名
            file_path = Path(root) / file
            if file_path.suffix.lower() in extensions:
                code_files.append(file_path)
    
    return sorted(code_files)


def count_lines(file_path):
    """统计文件行数"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except Exception:
        return 0


def remove_blank_lines(content):
    """移除空行"""
    lines = content.split('\n')
    non_blank_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_blank_lines)


def remove_sensitive_info(content):
    """移除敏感信息（简单处理）"""
    # 移除可能的密码/密钥（简化处理，实际使用时可能需要更复杂的规则）
    patterns = [
        (r'(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']', r'\1="***"'),
        (r'(secret|api[_-]?key|token)\s*[=:]\s*["\'][^"\']+["\']', r'\1="***"'),
        (r'(jdbc:|mysql://|postgresql://)[^\s"\']+', r'\1***'),
    ]
    
    for pattern, repl in patterns:
        content = re.sub(pattern, repl, content, flags=re.IGNORECASE)
    
    return content


def read_file_content(file_path, remove_blank=True, desensitize=True):
    """读取文件内容并进行处理"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if remove_blank:
            content = remove_blank_lines(content)
        
        if desensitize:
            content = remove_sensitive_info(content)
        
        return content
    except Exception as e:
        return f"// Error reading file: {e}\n"


def collect_code_content(code_files, max_lines=None):
    """
    收集代码内容
    
    Args:
        code_files: 代码文件路径列表
        max_lines: 最大收集行数，None表示不限制
    
    Returns:
        str: 收集的代码内容
    """
    all_content = []
    total_lines = 0
    
    for file_path in code_files:
        # 添加文件分隔注释
        relative_path = file_path.name
        separator = f"\n// {'='*60}\n// File: {relative_path}\n// {'='*60}\n\n"
        
        content = read_file_content(file_path)
        file_lines = content.count('\n') + 1
        
        if max_lines and total_lines + file_lines > max_lines:
            # 只取需要的部分
            remaining = max_lines - total_lines
            lines = content.split('\n')[:remaining]
            content = '\n'.join(lines)
            all_content.append(separator + content)
            break
        
        all_content.append(separator + content)
        total_lines += file_lines
    
    return '\n'.join(all_content)


def split_into_pages(content, lines_per_page=50):
    """
    将代码内容按指定行数分页
    
    Args:
        content: 代码内容
        lines_per_page: 每页行数
    
    Returns:
        list: 每页内容的列表
    """
    lines = content.split('\n')
    pages = []
    
    for i in range(0, len(lines), lines_per_page):
        page_lines = lines[i:i + lines_per_page]
        # 如果最后一页不足，用空行补齐（实际应删除空行）
        while len(page_lines) < lines_per_page:
            page_lines.append('')
        pages.append('\n'.join(page_lines))
    
    return pages


def generate_document(pages, software_name, version, output_path, pages_per_doc=30):
    """
    生成Word格式的源代码文档
    
    Args:
        pages: 页面内容列表
        software_name: 软件名称
        version: 版本号
        output_path: 输出文件路径
        pages_per_doc: 每个文档的页数
    """
    try:
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        print("错误：需要安装 python-docx 库")
        print("请运行: pip install python-docx")
        return False
    
    doc = Document()
    
    # 设置页面边距
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.25)
    
    # 设置页眉
    header = sections[0].header
    header_para = header.paragraphs[0]
    header_para.text = f"{software_name} {version}"
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_run = header_para.runs[0]
    header_run.font.size = Pt(9)
    header_run.font.name = '宋体'
    
    # 添加页面内容
    for i, page_content in enumerate(pages[:pages_per_doc]):
        if i > 0:
            doc.add_page_break()
        
        # 添加页码（右侧）
        # 注意：python-docx 对页码支持有限，需要手动处理或使用域代码
        
        # 添加代码内容
        paragraph = doc.add_paragraph()
        run = paragraph.add_run(page_content)
        run.font.name = 'Consolas'
        run.font.size = Pt(10.5)
        
        # 设置段落格式
        paragraph_format = paragraph.paragraph_format
        paragraph_format.line_spacing = Pt(12)
        paragraph_format.space_after = Pt(0)
    
    # 保存文档
    doc.save(output_path)
    return True


def generate_text_document(pages, software_name, version, output_path, pages_per_doc=30):
    """
    生成纯文本格式的源代码文档（备用方案）
    
    Args:
        pages: 页面内容列表
        software_name: 软件名称
        version: 版本号
        output_path: 输出文件路径
        pages_per_doc: 每个文档的页数
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入页眉说明
        f.write(f"软件名称：{software_name}\n")
        f.write(f"版本号：{version}\n")
        f.write(f"总页数：{min(len(pages), pages_per_doc)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, page_content in enumerate(pages[:pages_per_doc]):
            # 页眉
            header_line = f"{software_name} {version}"
            f.write(header_line.center(60) + f" {i+1}\n")
            f.write("-" * 60 + "\n")
            
            # 内容
            f.write(page_content + "\n")
            f.write("\n" + "=" * 60 + "\n\n")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='软著源代码提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python extract_source.py --project-path ./my-project --software-name "XX系统" --version "V1.0"
  
  # 自定义输出目录
  python extract_source.py -p ./my-project -n "XX系统" -v "V1.0" -o ./output
  
  # 自定义文件扩展名
  python extract_source.py -p ./my-project -n "XX系统" -v "V1.0" --ext .java,.xml,.properties
  
  # 指定自定义的前后30页代码
  python extract_source.py -p ./my-project -n "XX系统" -v "V1.0" \\
      --front-pages ./custom/front.txt --back-pages ./custom/back.txt
        """
    )
    
    parser.add_argument('-p', '--project-path', required=True,
                        help='项目根目录路径')
    parser.add_argument('-n', '--software-name', required=True,
                        help='软件全称（用于页眉）')
    parser.add_argument('-v', '--version', required=True,
                        help='版本号（用于页眉，如 V1.0）')
    parser.add_argument('-o', '--output-dir', default='./软著源代码',
                        help='输出目录（默认: ./软著源代码）')
    parser.add_argument('--ext', type=str,
                        help='包含的文件扩展名，逗号分隔（如: .java,.xml）')
    parser.add_argument('--exclude-dirs', type=str,
                        help='排除的目录，逗号分隔')
    parser.add_argument('--exclude-files', type=str,
                        help='排除的文件，逗号分隔')
    parser.add_argument('--lines-per-page', type=int, default=50,
                        help='每页行数（默认: 50）')
    parser.add_argument('--front-pages', type=str,
                        help='自定义前30页代码文件路径')
    parser.add_argument('--back-pages', type=str,
                        help='自定义后30页代码文件路径')
    parser.add_argument('--format', choices=['auto', 'docx', 'txt'], default='auto',
                        help='输出格式（默认: auto，优先docx）')
    
    args = parser.parse_args()
    
    # 解析扩展名
    if args.ext:
        extensions = set(ext.strip() for ext in args.ext.split(','))
    else:
        extensions = DEFAULT_EXTENSIONS
    
    # 解析排除项
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
    if args.exclude_dirs:
        exclude_dirs.update(d.strip() for d in args.exclude_dirs.split(','))
    
    exclude_files = DEFAULT_EXCLUDE_FILES.copy()
    if args.exclude_files:
        exclude_files.update(f.strip() for f in args.exclude_files.split(','))
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"正在扫描项目: {args.project_path}")
    print(f"文件扩展名: {extensions}")
    
    # 获取所有代码文件
    code_files = get_all_code_files(
        args.project_path,
        extensions=extensions,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files
    )
    
    print(f"找到 {len(code_files)} 个代码文件")
    
    if not code_files:
        print("错误：未找到任何代码文件，请检查项目路径和扩展名设置")
        return
    
    # 统计总代码行数
    total_lines = sum(count_lines(f) for f in code_files)
    print(f"总代码行数: {total_lines}")
    
    # 生成前30页
    print("\n正在生成前30页源代码...")
    if args.front_pages and Path(args.front_pages).exists():
        # 使用自定义前30页
        with open(args.front_pages, 'r', encoding='utf-8') as f:
            front_content = f.read()
        front_pages = split_into_pages(front_content, args.lines_per_page)
        print(f"使用自定义前30页: {args.front_pages}")
    else:
        # 从项目中提取
        # 优先选择：配置文件 -> 入口文件 -> 核心模块
        priority_files = []
        other_files = []
        
        config_patterns = ['package.json', 'pom.xml', 'build.gradle', 'requirements.txt', 
                          'Cargo.toml', 'go.mod', 'composer.json', 'Gemfile']
        main_patterns = ['main', 'app', 'index', 'application', 'startup']
        
        for f in code_files:
            fname = f.name.lower()
            if any(cp in fname for cp in config_patterns):
                priority_files.append(f)
            elif any(mp in fname for mp in main_patterns):
                priority_files.append(f)
            else:
                other_files.append(f)
        
        # 合并文件列表（配置文件优先，然后按字母顺序）
        sorted_files = priority_files + other_files
        front_content = collect_code_content(sorted_files, max_lines=30 * args.lines_per_page)
        front_pages = split_into_pages(front_content, args.lines_per_page)
    
    # 生成后30页
    print("正在生成后30页源代码...")
    if args.back_pages and Path(args.back_pages).exists():
        # 使用自定义后30页
        with open(args.back_pages, 'r', encoding='utf-8') as f:
            back_content = f.read()
        back_pages = split_into_pages(back_content, args.lines_per_page)
        print(f"使用自定义后30页: {args.back_pages}")
    else:
        # 从项目中倒序提取
        reversed_files = list(reversed(code_files))
        back_content = collect_code_content(reversed_files, max_lines=30 * args.lines_per_page)
        back_pages = split_into_pages(back_content, args.lines_per_page)
    
    # 确定输出格式
    use_docx = args.format == 'docx'
    if args.format == 'auto':
        try:
            from docx import Document
            use_docx = True
        except ImportError:
            use_docx = False
            print("注意：未安装 python-docx，将使用纯文本格式输出")
            print("如需Word格式，请运行: pip install python-docx")
    
    # 生成文档
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if use_docx:
        # 生成Word文档
        front_path = output_dir / f"源代码_前30页_{timestamp}.docx"
        back_path = output_dir / f"源代码_后30页_{timestamp}.docx"
        
        print(f"\n生成Word文档...")
        generate_document(front_pages, args.software_name, args.version, front_path, 30)
        generate_document(back_pages, args.software_name, args.version, back_path, 30)
        
        print(f"前30页: {front_path}")
        print(f"后30页: {back_path}")
    else:
        # 生成纯文本文档
        front_path = output_dir / f"源代码_前30页_{timestamp}.txt"
        back_path = output_dir / f"源代码_后30页_{timestamp}.txt"
        
        print(f"\n生成文本文档...")
        generate_text_document(front_pages, args.software_name, args.version, front_path, 30)
        generate_text_document(back_pages, args.software_name, args.version, back_path, 30)
        
        print(f"前30页: {front_path}")
        print(f"后30页: {back_path}")
        print("\n提示：文本格式需要手动粘贴到Word中并调整格式")
    
    # 生成统计信息
    info_path = output_dir / f"统计信息_{timestamp}.txt"
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(f"软件名称: {args.software_name}\n")
        f.write(f"版本号: {args.version}\n")
        f.write(f"项目路径: {args.project_path}\n")
        f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n统计信息:\n")
        f.write(f"  代码文件总数: {len(code_files)}\n")
        f.write(f"  总代码行数: {total_lines}\n")
        f.write(f"  平均每文件行数: {total_lines // len(code_files) if code_files else 0}\n")
        f.write(f"\n文件扩展名分布:\n")
        
        ext_count = {}
        for f in code_files:
            ext = f.suffix.lower()
            ext_count[ext] = ext_count.get(ext, 0) + 1
        
        for ext, count in sorted(ext_count.items(), key=lambda x: -x[1]):
            f.write(f"  {ext}: {count} 个文件\n")
        
        f.write(f"\n前30页来源:\n")
        if args.front_pages:
            f.write(f"  自定义文件: {args.front_pages}\n")
        else:
            f.write(f"  自动从项目提取（前{min(30, len(front_pages))}页）\n")
        
        f.write(f"\n后30页来源:\n")
        if args.back_pages:
            f.write(f"  自定义文件: {args.back_pages}\n")
        else:
            f.write(f"  自动从项目提取（后{min(30, len(back_pages))}页）\n")
    
    print(f"\n统计信息: {info_path}")
    print("\n完成！请检查生成的文档并按需要调整格式。")
    print("注意：生成的文档可能需要进一步调整以完全符合要求")


if __name__ == '__main__':
    main()
