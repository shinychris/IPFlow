#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利文档格式化工具

功能：
1. 统计专利文档字数（用于摘要300字限制检查）
2. 检查权利要求编号连续性
3. 检查说明书结构完整性
4. 生成专利文档统计报告

使用方法:
    python patent_formatter.py --file /path/to/patent.md --type invention
    python patent_formatter.py --file /path/to/claims.txt --check-claims
"""

import re
import argparse
from pathlib import Path
from collections import defaultdict


def count_chinese_chars(text):
    """统计中文字符数（含标点）"""
    # 中文字符范围
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]')
    return len(chinese_pattern.findall(text))


def count_total_chars(text):
    """统计总字符数（含中英文、数字、标点）"""
    return len(text.replace('\n', '').replace(' ', ''))


def check_claims_numbering(text):
    """检查权利要求编号"""
    # 匹配权利要求编号
    pattern = r'^[\s]*([0-9]+)[\.、\s]+'
    lines = text.split('\n')
    
    claims = []
    for line in lines:
        match = re.match(pattern, line.strip())
        if match:
            claims.append(int(match.group(1)))
    
    # 检查连续性
    issues = []
    if not claims:
        issues.append("未找到权利要求编号")
        return issues, claims
    
    # 检查是否从1开始
    if claims[0] != 1:
        issues.append(f"权利要求应从1开始，实际从{claims[0]}开始")
    
    # 检查连续性
    for i in range(1, len(claims)):
        if claims[i] != claims[i-1] + 1:
            issues.append(f"权利要求编号不连续：{claims[i-1]} 之后是 {claims[i]}")
    
    # 检查重复
    seen = set()
    for num in claims:
        if num in seen:
            issues.append(f"权利要求编号重复：{num}")
        seen.add(num)
    
    return issues, claims


def check_claims_references(text):
    """检查权利要求引用关系"""
    # 匹配引用关系
    pattern = r'根据权利要求([0-9]+(?:-[0-9]+)?|(?:[0-9]+或[0-9]+)+)'
    
    issues = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines, 1):
        match = re.search(pattern, line)
        if match:
            ref = match.group(1)
            # 检查是否为多项引用多项
            if '任一项' in line or '或' in ref:
                # 检查该从属权利要求是否被其他多项从属权利要求引用
                pass  # 复杂检查，暂时跳过
    
    return issues


def check_specification_structure(text):
    """检查说明书结构"""
    required_sections = [
        ('技术领域', r'技术领域'),
        ('背景技术', r'背景技术'),
        ('发明内容', r'发明内容|实用新型内容'),
        ('附图说明', r'附图说明'),
        ('具体实施方式', r'具体实施方式'),
    ]
    
    missing = []
    found = []
    
    for name, pattern in required_sections:
        if re.search(pattern, text):
            found.append(name)
        else:
            missing.append(name)
    
    return found, missing


def check_abstract_length(text):
    """检查摘要字数"""
    # 提取摘要部分
    abstract_pattern = r'说明书摘要\s*\n?(.*?)(?=\n\s*\n|$)'
    match = re.search(abstract_pattern, text, re.DOTALL)
    
    if not match:
        return None, "未找到说明书摘要"
    
    abstract = match.group(1).strip()
    char_count = count_chinese_chars(abstract)
    
    return char_count, abstract


def analyze_patent_file(file_path, patent_type='invention'):
    """分析专利文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    report = []
    report.append("=" * 60)
    report.append(f"专利文档分析报告")
    report.append(f"文件：{file_path}")
    report.append(f"类型：{patent_type}")
    report.append("=" * 60)
    
    # 1. 统计字数
    report.append("\n【字数统计】")
    total_chars = count_total_chars(content)
    chinese_chars = count_chinese_chars(content)
    report.append(f"总字符数：{total_chars}")
    report.append(f"中文字符数（含标点）：{chinese_chars}")
    
    # 2. 检查摘要
    report.append("\n【摘要检查】")
    abstract_len, abstract = check_abstract_length(content)
    if abstract_len:
        report.append(f"摘要字数：{abstract_len}")
        if abstract_len > 300:
            report.append(f"⚠️ 警告：摘要超过300字限制（超出{abstract_len-300}字）")
        else:
            report.append(f"✓ 摘要字数符合要求（剩余{300-abstract_len}字）")
    else:
        report.append(f"⚠️ {abstract}")
    
    # 3. 检查说明书结构
    if patent_type in ['invention', 'utility']:
        report.append("\n【说明书结构检查】")
        found, missing = check_specification_structure(content)
        report.append(f"已找到章节：{', '.join(found)}")
        if missing:
            report.append(f"⚠️ 缺失章节：{', '.join(missing)}")
        else:
            report.append("✓ 说明书结构完整")
    
    # 4. 检查权利要求
    report.append("\n【权利要求检查】")
    issues, claims = check_claims_numbering(content)
    if claims:
        report.append(f"权利要求总数：{len(claims)}")
        report.append(f"权利要求编号：{claims}")
        if issues:
            for issue in issues:
                report.append(f"⚠️ {issue}")
        else:
            report.append("✓ 权利要求编号正确")
    else:
        report.append("⚠️ 未找到权利要求")
    
    # 5. 检查独立/从属权利要求
    if claims:
        independent_claims = []
        dependent_claims = []
        lines = content.split('\n')
        
        for line in lines:
            match = re.match(r'^[\s]*([0-9]+)[\.、\s]+', line.strip())
            if match:
                num = int(match.group(1))
                if '根据权利要求' in line or '如权利要求' in line:
                    dependent_claims.append(num)
                else:
                    independent_claims.append(num)
        
        report.append(f"\n独立权利要求：{independent_claims}")
        report.append(f"从属权利要求：{dependent_claims}")
    
    # 6. 检查附图标记
    report.append("\n【附图标记检查】")
    figure_refs = re.findall(r'（\s*([0-9]+)\s*）', content)
    if figure_refs:
        unique_refs = sorted(set(int(x) for x in figure_refs))
        report.append(f"附图标记数量：{len(unique_refs)} 个")
        report.append(f"附图标记：{unique_refs}")
    else:
        report.append("⚠️ 未找到附图标记")
    
    report.append("\n" + "=" * 60)
    
    return '\n'.join(report)


def format_patent_file(file_path, output_path=None):
    """格式化专利文件（添加页眉等）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 这里可以添加格式化逻辑
    # 如：添加页眉、页脚、页码等
    
    formatted = content
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted)
        print(f"格式化后的文件已保存至：{output_path}")
    
    return formatted


def main():
    parser = argparse.ArgumentParser(
        description='专利文档格式化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析发明专利文件
  python patent_formatter.py --file invention.md --type invention
  
  # 分析实用新型文件
  python patent_formatter.py --file utility.md --type utility
  
  # 仅检查权利要求
  python patent_formatter.py --file claims.txt --check-claims
  
  # 输出报告到文件
  python patent_formatter.py --file patent.md --output report.txt
        """
    )
    
    parser.add_argument('-f', '--file', required=True,
                        help='专利文件路径')
    parser.add_argument('-t', '--type', 
                        choices=['invention', 'utility', 'design'],
                        default='invention',
                        help='专利类型（默认：invention）')
    parser.add_argument('-o', '--output',
                        help='输出报告文件路径')
    parser.add_argument('--check-claims', action='store_true',
                        help='仅检查权利要求')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"错误：文件不存在：{args.file}")
        return
    
    if args.check_claims:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        issues, claims = check_claims_numbering(content)
        print(f"权利要求数量：{len(claims)}")
        print(f"权利要求编号：{claims}")
        if issues:
            print("\n存在的问题：")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ 权利要求编号正确")
    else:
        report = analyze_patent_file(args.file, args.type)
        print(report)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n报告已保存至：{args.output}")


if __name__ == '__main__':
    main()
