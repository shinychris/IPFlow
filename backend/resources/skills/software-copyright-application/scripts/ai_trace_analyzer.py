#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软著材料 AI 痕迹分析工具

快速自检源代码或用户手册的 AI 特征指标，输出 AI 风险评分与改进建议。
仅使用 Python 标准库，无需安装额外依赖。

软著硬性指标：
  - 源代码注释覆盖率必须 <5%（最强 AI 指纹）
  - AI 风险评分 <30（低风险，接近人类特征）

详细策略参考: references/anti-ai-detection.md

使用方法:
    # 分析源代码文档
    python ai_trace_analyzer.py --type code --path ./source-code-front.docx

    # 分析用户手册
    python ai_trace_analyzer.py --type text --path ./user-manual.docx

    # 批量分析目录下所有 .md/.txt/.docx 文件
    python ai_trace_analyzer.py --type text --path ./materials/ --batch
"""

import os
import re
import argparse
from pathlib import Path
from math import sqrt


# AI 常见的中文连接词（基于 references/anti-ai-detection.md 总结）
AI_CONNECTORS_CN = {
    '因此', '此外', '值得注意的是', '综上所述', '显而易见',
    '总而言之', '换言之', '与此同时', '不仅如此', '由此可见',
    '首先', '其次', '然后', '最后', '另外', '另一方面',
    '需要指出的是', '毋庸置疑', '诚然',
}

# AI 常见的英文过渡词
AI_CONNECTORS_EN = {
    'therefore', 'moreover', 'furthermore', 'however', 'nevertheless',
    'additionally', 'consequently', 'subsequently', 'thus', 'hence',
    'overall', 'in conclusion', 'in summary',
}

# 代码注释起始模式（覆盖主流语言）
COMMENT_PATTERNS = [
    re.compile(r'^\s*#'),                       # Python/Ruby/Shell
    re.compile(r'^\s*//'),                      # C/Java/JS/Go/Rust
    re.compile(r'^\s*/\*'),                     # C 风格块注释开始
    re.compile(r'^\s*\*'),                      # 块注释续行
    re.compile(r'^\s*<!--'),                    # HTML/XML
    re.compile(r'^\s*--'),                      # SQL/Lua
    re.compile(r'^\s*"""'),                     # Python 文档字符串
    re.compile(r"^\s*'''"),
]

# 个人风格标记（人类程序员常用）
HUMAN_MARKERS = ['TODO', 'FIXME', 'HACK', 'XXX', 'NOTE', '临时', '待优化', '后续重构']

# 英文 message 检测模式：提取 throw/Exception/message/alert/showToast/title 等附近的英文文案
EN_MESSAGE_PATTERNS = [
    # throw new XxxException("英文文案") / raise XxxError("英文文案")
    re.compile(r'(?:throw\s+\w*Exception|raise\s+\w*Error)\s*\(\s*["\']([A-Za-z][A-Za-z\s,\.!?\d]{3,})["\']'),
    # message: "英文文案" / message = "英文文案" / msg: "英文文案"
    re.compile(r'\b(?:message|msg)\s*[:=]\s*["\']([A-Za-z][A-Za-z\s,\.!?\d]{3,})["\']'),
    # alert("英文") / confirm("英文") / prompt("英文")
    re.compile(r'\b(?:alert|confirm|prompt)\s*\(\s*["\']([A-Za-z][A-Za-z\s,\.!?\d]{3,})["\']'),
    # title/content/tip: "英文"（常用于小程序 showToast）
    re.compile(r'\b(?:title|content|tip)\s*:\s*["\']([A-Za-z][A-Za-z\s,\.!?\d]{3,})["\']'),
    # return { ..., message: "英文" }
    re.compile(r'return\s*\{[^}]*\bmessage\b[^}]*["\']([A-Za-z][A-Za-z\s,\.!?\d]{3,})["\']'),
]

# 注释中允许保留的英文（技术术语/缩写，全大写或常见专有名词）
ALLOWED_EN_TERMS = {
    'API', 'HTTP', 'HTTPS', 'URL', 'URI', 'JSON', 'XML', 'SQL', 'HTML', 'CSS',
    'JWT', 'OAuth', 'TCP', 'UDP', 'DNS', 'CDN', 'SSL', 'TLS', 'REST', 'SOAP',
    'CPU', 'RAM', 'GPU', 'IO', 'OS', 'DB', 'CRUD', 'MVC', 'MVVM', 'ORM',
    'TODO', 'FIXME', 'HACK', 'XXX', 'NOTE', 'WIP',
    'ID', 'UUID', 'GUID', 'IP', 'MAC', 'PC',
}

# 常见英文功能词（出现这些词强烈暗示注释是英文）
EN_COMMON_WORDS = {
    'the', 'this', 'that', 'these', 'those', 'a', 'an', 'is', 'are', 'was',
    'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must',
    'if', 'else', 'then', 'when', 'where', 'why', 'how', 'what', 'which',
    'for', 'to', 'of', 'in', 'on', 'at', 'by', 'with', 'from', 'into',
    'and', 'or', 'but', 'not', 'no', 'yes', 'so', 'as', 'than',
    'function', 'method', 'class', 'return', 'check', 'get', 'set', 'add',
    'remove', 'update', 'delete', 'create', 'init', 'handle', 'process',
    'here', 'there', 'it', 'we', 'you', 'they', 'he', 'she',
    'use', 'used', 'using', 'user', 'data', 'value', 'type', 'name',
    'file', 'line', 'code', 'test', 'fix', 'error', 'success', 'fail',
}


def read_text(path: str) -> str:
    """读取文本/docx 文件，尝试多种编码；docx 用 python-docx 提取纯文本"""
    p = Path(path)
    # docx 文件：用 python-docx 提取段落文本
    if p.suffix.lower() == '.docx':
        try:
            from docx import Document
            doc = Document(path)
            return '\n'.join(para.text for para in doc.paragraphs)
        except ImportError:
            raise RuntimeError(
                f"读取 .docx 需要安装 python-docx：pip install python-docx（文件: {path}）"
            )
        except Exception as e:
            raise RuntimeError(f"读取 docx 失败 {path}: {e}")

    # 普通文本文件
    for encoding in ('utf-8', 'gbk', 'utf-8-sig'):
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法解码文件: {path}")


# ============================================================
# 代码分析
# ============================================================

def _extract_code_blocks(text: str) -> str:
    """从 markdown 文本中提取所有代码块（``` 包裹）内容，避免把 # 标题、* 列表误判为注释"""
    blocks = []
    in_block = False
    for line in text.split('\n'):
        if line.strip().startswith('```'):
            in_block = not in_block
            continue
        if in_block:
            blocks.append(line)
    return '\n'.join(blocks)


def detect_english_messages(text: str) -> list:
    """检测代码中的英文 message 文案（应改成中文）

    返回匹配到的英文文案列表。
    """
    found = []
    for pattern in EN_MESSAGE_PATTERNS:
        for m in pattern.findall(text):
            content = m.strip()
            # 文案中英文字母占比高（>60%）才判定为英文 message
            letters = sum(1 for c in content if c.isalpha())
            if letters and letters / max(len(content), 1) > 0.6:
                found.append(content)
    return found


def detect_english_comments(lines: list) -> list:
    """检测注释中的英文（排除函数名/类名/技术术语）

    Args:
        lines: 代码行列表
    Returns:
        违规的注释行列表（行内容）
    """
    violations = []
    for line in lines:
        # 仅检查注释行
        if not any(p.match(line) for p in COMMENT_PATTERNS):
            continue
        # 去除注释符号
        cleaned = re.sub(r'^\s*(//|#|--|/\*|\*|<!--|-->|#)\s*', '', line).strip()
        # 提取英文单词
        words = re.findall(r'[a-zA-Z]+', cleaned)
        # 过滤：允许的术语（全大写）、标识符引用
        suspect = []
        for w in words:
            wl = w.lower()
            # 全大写缩写（2字母以上）视为术语，放过
            if len(w) >= 2 and w.isupper():
                continue
            # 命中常见英文功能词，强烈暗示英文注释
            if wl in EN_COMMON_WORDS:
                suspect.append(w)
        # 累计 2 个以上常见英文词，判定为英文注释
        if len(suspect) >= 2:
            violations.append(line.rstrip())
    return violations


def analyze_code(text: str, is_markdown: bool = False) -> dict:
    """分析代码的 AI 特征

    Args:
        text: 代码文本
        is_markdown: 若为 True（.md 文件），只统计 ``` 代码块内的内容，
                     避免 markdown 的 # 标题、* 列表被误判为注释
    """
    if is_markdown:
        text = _extract_code_blocks(text)

    lines = text.split('\n')
    non_blank_lines = [ln for ln in lines if ln.strip()]
    if not non_blank_lines:
        return {'error': '文件为空' + ('（或代码块为空）' if is_markdown else '')}

    total = len(non_blank_lines)
    comment_lines = sum(
        1 for ln in non_blank_lines
        if any(p.match(ln) for p in COMMENT_PATTERNS)
    )
    comment_ratio = comment_lines / total

    # 个人标记数量
    marker_count = sum(text.count(m) for m in HUMAN_MARKERS)

    # 函数定义统计（覆盖主流语言）
    func_pattern = re.compile(
        r'^\s*(?:public|private|protected|static|async|def|function|func|fn|fun)\s+'
        r'(?:[\w<>?,\s]+)\s+(\w+)\s*\(',
        re.MULTILINE
    )
    func_names = func_pattern.findall(text)

    # 命名规范度：完整语义命名（多单词 camelCase 或 snake_case）占比
    long_names = [n for n in func_names if len(n) >= 12]
    long_name_ratio = len(long_names) / max(len(func_names), 1)

    # 平均函数长度（粗略估算：从 def 到下一个 def）
    func_lengths = []
    if func_names:
        func_positions = [m.start() for m in func_pattern.finditer(text)]
        for i, pos in enumerate(func_positions):
            end = func_positions[i + 1] if i + 1 < len(func_positions) else len(text)
            body = text[pos:end]
            func_lengths.append(len([ln for ln in body.split('\n') if ln.strip()]))

    avg_func_len = sum(func_lengths) / len(func_lengths) if func_lengths else 0
    func_len_variance = (
        sqrt(sum((x - avg_func_len) ** 2 for x in func_lengths) / len(func_lengths))
        if len(func_lengths) > 1 else 0
    )

    # 评估（软著硬性指标：注释率 <5%）
    risks = []
    if comment_ratio >= 0.05:
        risks.append(f"注释覆盖率 {comment_ratio:.1%} 超标（软著硬性要求 <5%，AI 特征 80-90%，人类 20-40%）")
    elif comment_ratio >= 0.03:
        risks.append(f"注释覆盖率 {comment_ratio:.1%} 偏高（建议进一步削减到 <3%）")
    if long_name_ratio > 0.7 and len(func_names) >= 3:
        risks.append(f"函数命名过于规范 {long_name_ratio:.1%}（缺少缩写/简称）")
    if marker_count == 0 and total > 100:
        risks.append("无 TODO/FIXME 等个人风格标记（AI 代码特征）")
    if 20 <= avg_func_len <= 40 and func_len_variance < 5 and len(func_lengths) >= 5:
        risks.append(f"函数长度过于均匀（平均 {avg_func_len:.0f} 行，方差 {func_len_variance:.1f}）")

    # 英文 message 检测（软著规范：message 必须中文）
    en_messages = detect_english_messages(text)
    if en_messages:
        sample = '、'.join(f'"{m}"' for m in en_messages[:3])
        more = f' 等 {len(en_messages)} 处' if len(en_messages) > 3 else ''
        risks.append(f"代码中存在英文 message 文案{more}（必须改成中文）：{sample}")

    # 英文注释检测（软著规范：注释除专用语外禁止英文）
    en_comments = detect_english_comments(non_blank_lines)
    if en_comments:
        sample = en_comments[0].strip()[:50]
        more = f' 等 {len(en_comments)} 行' if len(en_comments) > 1 else ''
        risks.append(f"注释中存在英文{more}（除函数名/术语外禁止英文）：{sample}")

    # AI 风险评分（0-100，越高越像 AI）
    # 注释率是软著最强指纹，权重最高（40 分），>5% 直接严重扣分
    score = 0
    if comment_ratio >= 0.05:
        # 超标：按比例扣分，>20% 几乎满分
        score += min(40, comment_ratio * 200)
    elif comment_ratio >= 0.03:
        score += 12  # 临界，轻扣
    score += min(15, long_name_ratio * 15)                 # 命名贡献 15
    score += 10 if marker_count == 0 and total > 100 else 0
    score += min(10, max(0, (10 - func_len_variance)))     # 函数长度方差贡献 10
    # 英文 message / 英文注释：各贡献 10 分（中文化硬性规范）
    score += min(10, len(en_messages) * 5)                  # 英文 message
    score += min(10, len(en_comments) * 3)                  # 英文注释
    score = min(100, score)

    return {
        'total_lines': total,
        'comment_lines': comment_lines,
        'comment_ratio': f"{comment_ratio:.1%}",
        'function_count': len(func_names),
        'avg_function_length': f"{avg_func_len:.1f} 行",
        'function_length_variance': f"{func_len_variance:.1f}",
        'human_markers': marker_count,
        'english_messages': len(en_messages),
        'english_comments': len(en_comments),
        'ai_risk_score': f"{score:.0f} / 100",
        'risk_level': _risk_level(score),
        'risks': risks,
        'suggestions': _code_suggestions(risks),
    }


def _code_suggestions(risks: list) -> list:
    """根据风险生成改进建议"""
    suggestions = []
    if any('超标' in r and '注释覆盖率' in r for r in risks):
        suggestions.append("⚠️ 注释率超标（软著硬性 <5%）：删除一切显而易见的注释，仅保留复杂算法/关键业务规则；严禁统一 JSDoc/JavaDoc 块注释")
    elif any('偏高' in r and '注释覆盖率' in r for r in risks):
        suggestions.append("注释率临界（建议 <3%）：再削减部分注释，只留最关键的算法/业务说明")
    if any('命名过于规范' in r for r in risks):
        suggestions.append("将部分长函数名改为缩写：如 userAuthenticationToken → uauthToken")
    if any('个人风格标记' in r for r in risks):
        suggestions.append("添加 TODO/FIXME/HACK 标记，如 '// TODO: 这里需要优化，先临时这样处理'")
    if any('函数长度过于均匀' in r for r in risks):
        suggestions.append("合并部分小函数为大函数（50-100行），同时拆分完美长函数为不均匀短函数")
    if any('英文 message' in r for r in risks):
        suggestions.append("⚠️ message 中文化：所有提示/异常文案改成中文，如 'User not found' → '用户不存在'")
    if any('注释中存在英文' in r for r in risks):
        suggestions.append("⚠️ 注释中文化：注释改用中文书写（函数名/类名/术语可保留英文），如 '// check user' → '// 检查用户'")
    if not risks:
        suggestions.append("代码已具备较好的人工特征，建议做最终润色确认")
    return suggestions


# ============================================================
# 文本分析
# ============================================================

def analyze_text(text: str) -> dict:
    """分析文本（用户手册）的 AI 特征"""
    # 按中文/英文句号、问号、感叹号切分
    sentences = re.split(r'[。！？!?\.]\s*', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 3]

    if not sentences:
        return {'error': '未识别到有效句子'}

    # 句长（按字符数）
    lengths = [len(s) for s in sentences]
    avg_len = sum(lengths) / len(lengths)
    len_variance = sqrt(
        sum((x - avg_len) ** 2 for x in lengths) / len(lengths)
    ) if len(lengths) > 1 else 0

    # 连接词密度（每千字中 AI 连接词出现次数）
    total_chars = len(text)
    connector_count = 0
    for w in AI_CONNECTORS_CN:
        connector_count += len(re.findall(w, text))
    for w in AI_CONNECTORS_EN:
        connector_count += len(re.findall(r'\b' + w + r'\b', text, re.IGNORECASE))
    connector_density = connector_count / max(total_chars / 1000, 0.001)

    # 词汇多样性 TTR（去重 token 数 / 总 token 数）
    tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', text)
    unique = len(set(tokens))
    ttr = unique / max(len(tokens), 1)

    # 段落长度一致性
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) > 1:
        p_lengths = [len(p) for p in paragraphs]
        p_avg = sum(p_lengths) / len(p_lengths)
        p_cv = sqrt(sum((x - p_avg) ** 2 for x in p_lengths) / len(p_lengths)) / max(p_avg, 1)
        paragraph_consistency = f"{max(0, (1 - p_cv) * 100):.0f}%"
    else:
        paragraph_consistency = "N/A"

    # 评估
    risks = []
    if len_variance < 10:
        risks.append(f"句长方差过小（{len_variance:.1f}）：句式过于规整，缺乏长短句交替")
    if connector_density > 8:
        risks.append(f"AI 连接词密度过高（{connector_density:.1f}/千字）：建议用'话说回来'、'不过要注意'等口语化表达替代")
    if ttr < 0.5:
        risks.append(f"词汇多样性不足（TTR={ttr:.2f}）：倾向使用'安全'词汇，缺少长尾词")
    if paragraph_consistency != "N/A" and float(paragraph_consistency.strip('%')) > 85:
        risks.append(f"段落长度过于一致（{paragraph_consistency}）：缺少段落长度差异")

    # 人工痕迹检查
    human_signs = sum(1 for m in ['💡', '⚠️', '笔者', '我建议', '我们', '你', '小贴士']
                      if m in text)
    if human_signs < 2:
        risks.append("缺少人工痕迹（建议添加 💡/⚠️ 标记、个人经验、第二人称'你'）")

    # AI 风险评分
    score = 0
    score += min(25, max(0, (15 - len_variance)))         # 句长方差
    score += min(25, max(0, (connector_density - 4) * 4))  # 连接词
    score += min(20, max(0, (0.6 - ttr) * 40))             # TTR
    score += min(15, max(0, human_signs < 2 and 15 or 0))  # 人工痕迹
    score += min(15, max(0, (float(paragraph_consistency.strip('%')) - 70) * 0.5)
                 if paragraph_consistency != "N/A" else 0)
    score = min(100, score)

    return {
        'sentence_count': len(sentences),
        'avg_sentence_length': f"{avg_len:.1f} 字",
        'sentence_length_variance': f"{len_variance:.1f}",
        'ai_connector_count': connector_count,
        'connector_density': f"{connector_density:.1f} /千字",
        'ttr': f"{ttr:.3f}",
        'paragraph_consistency': paragraph_consistency,
        'human_signs': human_signs,
        'ai_risk_score': f"{score:.0f} / 100",
        'risk_level': _risk_level(score),
        'risks': risks,
        'suggestions': _text_suggestions(risks),
    }


def _text_suggestions(risks: list) -> list:
    """根据风险生成文本改进建议"""
    suggestions = []
    if any('句长方差过小' in r for r in risks):
        suggestions.append("长短句交替：将均匀长句改造为长短组合，如'用户管理？该有的都有。增、删、改、查，一个不落。'")
    if any('连接词密度过高' in r for r in risks):
        suggestions.append("替换 AI 连接词：用'话说回来'、'顺便说一句'、'不过要注意'替代'此外'、'值得注意的是'、'综上所述'")
    if any('词汇多样性' in r for r in risks):
        suggestions.append("引入长尾词：避免重复使用同一表达，多用具体场景（'假设你是销售人员...'）替代抽象描述")
    if any('段落长度过于一致' in r for r in risks):
        suggestions.append("调整段落长度差异：让某些段落只有 1-2 句，某些段落 10 行以上")
    if any('缺少人工痕迹' in r for r in risks):
        suggestions.append("添加人工痕迹：💡 小贴士、⚠️ 注意事项、个人经验（'建议先备份数据，笔者曾经因为没备份丢过文件'）、TODO 标记")
    if not risks:
        suggestions.append("文本已具备较好的人工特征，建议做最终润色确认")
    return suggestions


def _risk_level(score: float) -> str:
    """风险等级判定"""
    if score < 30:
        return "🟢 低风险（接近人类特征）"
    elif score < 60:
        return "🟡 中等风险（建议改进）"
    else:
        return "🔴 高风险（强 AI 特征，需要深度改造）"


# ============================================================
# 输出格式化
# ============================================================

def print_report(file_path: str, result: dict, analysis_type: str) -> None:
    """格式化输出分析报告"""
    print(f"\n{'=' * 60}")
    print(f"📂 文件: {file_path}")
    print(f"🔍 类型: {analysis_type}")
    print(f"{'=' * 60}")

    if 'error' in result:
        print(f"❌ {result['error']}")
        return

    # 指标表
    print("\n📊 关键指标:")
    for key in result:
        if key in ('risks', 'suggestions'):
            continue
        label = {
            'total_lines': '代码总行数',
            'comment_lines': '注释行数',
            'comment_ratio': '注释覆盖率',
            'function_count': '函数数量',
            'avg_function_length': '平均函数长度',
            'function_length_variance': '函数长度方差',
            'human_markers': '人工标记数',
            'english_messages': '英文 message 数',
            'english_comments': '英文注释行数',
            'sentence_count': '句子数量',
            'avg_sentence_length': '平均句长',
            'sentence_length_variance': '句长方差',
            'ai_connector_count': 'AI 连接词总数',
            'connector_density': '连接词密度',
            'ttr': '词汇多样性 TTR',
            'paragraph_consistency': '段落长度一致性',
            'human_signs': '人工痕迹数',
            'ai_risk_score': '⭐ AI 风险评分',
            'risk_level': '⚠️ 风险等级',
        }.get(key, key)
        print(f"  {label:<20}: {result[key]}")

    # 风险清单
    if result.get('risks'):
        print("\n⚠️ 识别到的 AI 特征:")
        for i, r in enumerate(result['risks'], 1):
            print(f"  {i}. {r}")
    else:
        print("\n✅ 未识别到明显的 AI 特征")

    # 改进建议
    if result.get('suggestions'):
        print("\n💡 改进建议:")
        for i, s in enumerate(result['suggestions'], 1):
            print(f"  {i}. {s}")

    print(f"\n{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='软著材料 AI 痕迹分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
详细策略参考: references/anti-ai-detection.md

示例:
  %(prog)s --type code --path ./source-code-front.md
  %(prog)s --type text --path ./user-manual.md
  %(prog)s --type text --path ./materials/ --batch
        """
    )
    parser.add_argument('--type', choices=['code', 'text'], required=True,
                        help='分析类型: code=源代码, text=用户手册')
    parser.add_argument('--path', required=True, help='文件或目录路径')
    parser.add_argument('--batch', action='store_true', help='批量分析目录下所有 .md/.txt/.docx 文件')

    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"❌ 路径不存在: {path}")
        return

    if path.is_file():
        files = [path]
    elif args.batch:
        files = sorted(
            list(path.rglob('*.md')) + list(path.rglob('*.txt'))
            + list(path.rglob('*.docx'))
        )
        if not files:
            print(f"❌ 目录中未找到 .md/.txt/.docx 文件: {path}")
            return
    else:
        print("❌ 提供的是目录路径，请加 --batch 参数进行批量分析")
        return

    for f in files:
        text = read_text(str(f))
        if args.type == 'code':
            # .md 文件只统计代码块内的注释，避免 # 标题/* 列表被误判
            is_md = f.suffix.lower() == '.md'
            result = analyze_code(text, is_markdown=is_md)
        else:
            result = analyze_text(text)
        print_report(str(f), result, args.type)


if __name__ == '__main__':
    main()
