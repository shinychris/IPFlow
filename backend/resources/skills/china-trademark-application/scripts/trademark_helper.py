#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商标申请辅助工具

功能：
1. 尼斯分类查询（常见类别速查）
2. 商标图样尺寸检查
3. 申请费用计算
4. 商品/服务项目数量统计

使用方法:
    python trademark_helper.py --function classify --keyword 软件
    python trademark_helper.py --function check-image --file logo.jpg
    python trademark_helper.py --function calculate-fee --classes 3 --items 25
"""

import argparse
import os
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# 尼斯分类常见类别速查表
NICE_CLASSIFICATION = {
    "化工": [(1, "化学原料"), (2, "颜料油漆")],
    "日化": [(3, "日化用品")],
    "医药": [(5, "医药")],
    "金属": [(6, "金属材料")],
    "机械": [(7, "机械设备"), (8, "手工器械")],
    "电子": [(9, "科学仪器"), (11, "灯具空调")],
    "运输": [(12, "运输工具")],
    "珠宝": [(14, "珠宝钟表")],
    "乐器": [(15, "乐器")],
    "办公": [(16, "办公用品")],
    "橡胶": [(17, "橡胶制品")],
    "皮革": [(18, "皮革皮具")],
    "建筑": [(19, "建筑材料")],
    "家具": [(20, "家具")],
    "厨房": [(21, "厨房洁具")],
    "纺织": [(22, "绳网袋篷"), (23, "纱线丝"), (24, "布料床单")],
    "服装": [(25, "服装鞋帽"), (26, "纽扣拉链")],
    "地毯": [(27, "地毯席垫")],
    "健身": [(28, "健身器材")],
    "食品": [(29, "食品"), (30, "方便食品"), (31, "饲料种籽")],
    "饮料": [(32, "啤酒饮料"), (33, "酒")],
    "烟草": [(34, "烟草烟具")],
    "广告": [(35, "广告销售")],
    "金融": [(36, "金融物管")],
    "建筑服务": [(37, "建筑修理")],
    "通讯": [(38, "通讯服务")],
    "运输服务": [(39, "运输贮藏")],
    "加工": [(40, "材料加工")],
    "教育": [(41, "教育娱乐")],
    "科技": [(42, "技术服务")],
    "餐饮": [(43, "餐饮住宿")],
    "医疗": [(44, "医疗园艺")],
    "法律": [(45, "法律服务")],
}


# 尼斯分类详细说明
CLASS_DESCRIPTIONS = {
    1: "化学原料 - 工业化学品、肥料、灭火剂等",
    2: "颜料油漆 - 颜料、涂料、防锈剂等",
    3: "日化用品 - 化妆品、洗涤剂、牙膏、香料等",
    5: "医药 - 药品、医用制剂、卫生用品等",
    9: "科学仪器 - 电子设备、计算机软件、手机APP等",
    10: "医疗器械 - 医疗仪器、假肢、矫形用品等",
    11: "灯具空调 - 照明设备、加热设备、制冷设备等",
    16: "办公用品 - 纸制品、印刷品、文具等",
    18: "皮革皮具 - 皮革、箱包、伞、手杖等",
    20: "家具 - 家具、镜子、竹木工艺品等",
    21: "厨房洁具 - 家用器皿、梳子、刷子、瓷器等",
    25: "服装鞋帽 - 服装、鞋、帽、袜、手套、围巾等",
    29: "食品 - 肉、鱼、加工食品、腌制食品、蛋、奶等",
    30: "方便食品 - 咖啡、茶、糖、米、面、面包、糕点等",
    31: "饲料种籽 - 农业产品、活动物、新鲜水果蔬菜等",
    32: "啤酒饮料 - 啤酒、矿泉水、汽水、果汁等",
    33: "酒 - 含酒精的饮料",
    35: "广告销售 - 广告、商业经营、商业管理、零售服务等",
    36: "金融物管 - 金融、银行、保险、房地产等",
    37: "建筑修理 - 建筑施工、修理、安装服务等",
    38: "通讯服务 - 电信、信息传输、广播、互联网等",
    39: "运输贮藏 - 运输、商品包装和贮藏、旅行安排等",
    41: "教育娱乐 - 教育、培训、娱乐、文体活动等",
    42: "技术服务 - 科学技术服务、软件开发、工业设计等",
    43: "餐饮住宿 - 餐饮服务、临时住宿、酒店等",
    44: "医疗园艺 - 医疗服务、兽医服务、美容服务等",
    45: "法律服务 - 法律服务、安全服务、婚姻介绍等",
}


def search_classification(keyword):
    """根据关键词搜索尼斯分类"""
    results = []
    
    # 直接匹配类别号
    if keyword.isdigit():
        class_num = int(keyword)
        if class_num in CLASS_DESCRIPTIONS:
            results.append((class_num, CLASS_DESCRIPTIONS[class_num]))
        return results
    
    # 匹配关键词
    for key, classes in NICE_CLASSIFICATION.items():
        if keyword in key or key in keyword:
            for class_num, class_name in classes:
                if class_num in CLASS_DESCRIPTIONS:
                    results.append((class_num, CLASS_DESCRIPTIONS[class_num]))
    
    # 在详细描述中搜索
    for class_num, description in CLASS_DESCRIPTIONS.items():
        if keyword in description and (class_num, description) not in results:
            results.append((class_num, description))
    
    return results


def check_image_requirements(file_path):
    """检查商标图样是否符合要求"""
    if not HAS_PIL:
        return "错误：需要安装PIL库才能检查图片。请运行：pip install Pillow"
    
    try:
        img = Image.open(file_path)
        width, height = img.size
        file_size = os.path.getsize(file_path)
        file_format = img.format
        
        report = []
        report.append(f"文件：{file_path}")
        report.append(f"格式：{file_format}")
        report.append(f"尺寸：{width}×{height}像素")
        report.append(f"文件大小：{file_size/1024:.2f}KB")
        
        # 检查要求
        issues = []
        
        if file_format != 'JPEG':
            issues.append(f"格式要求：JPG，当前：{file_format}")
        
        if width < 400 or height < 400:
            issues.append(f"尺寸过小：最小400×400像素，当前{width}×{height}")
        
        if width > 1500 or height > 1500:
            issues.append(f"尺寸过大：最大1500×1500像素，当前{width}×{height}")
        
        if file_size > 2 * 1024 * 1024:
            issues.append(f"文件过大：最大2MB，当前{file_size/1024/1024:.2f}MB")
        
        if issues:
            report.append("\n⚠️ 存在的问题：")
            for issue in issues:
                report.append(f"  - {issue}")
        else:
            report.append("\n✓ 图片符合要求")
        
        return '\n'.join(report)
    
    except Exception as e:
        return f"错误：无法读取图片 - {str(e)}"


def calculate_fee(classes, items_per_class=None, electronic=True):
    """计算商标注册费用"""
    
    # 官费标准（2025年）
    base_fee_electronic = 270  # 电子申请每类
    base_fee_paper = 300  # 纸质申请每类
    extra_item_fee_electronic = 27  # 电子申请每超1项
    extra_item_fee_paper = 30  # 纸质申请每超1项
    
    base_fee = base_fee_electronic if electronic else base_fee_paper
    extra_fee = extra_item_fee_electronic if electronic else extra_item_fee_paper
    
    report = []
    report.append("=" * 50)
    report.append("商标注册费用计算")
    report.append("=" * 50)
    report.append(f"申请方式：{'电子申请' if electronic else '纸质申请'}")
    report.append(f"申请类别数：{classes}类")
    
    total_fee = 0
    
    if items_per_class:
        # 指定每类的项目数
        for i, items in enumerate(items_per_class, 1):
            class_fee = base_fee
            extra_items = max(0, items - 10)
            extra_fee_total = extra_items * extra_fee
            
            report.append(f"\n第{i}类：")
            report.append(f"  商品/服务项目：{items}项")
            report.append(f"  基础费用（10项以内）：{base_fee}元")
            if extra_items > 0:
                report.append(f"  超出项目：{extra_items}项 × {extra_fee}元 = {extra_fee_total}元")
            class_total = base_fee + extra_fee_total
            report.append(f"  小计：{class_total}元")
            total_fee += class_total
    else:
        # 假设每类10项以内
        total_fee = classes * base_fee
        report.append(f"\n假设每类10项以内")
        report.append(f"基础费用：{classes}类 × {base_fee}元 = {total_fee}元")
    
    report.append(f"\n{'=' * 50}")
    report.append(f"官费合计：{total_fee}元")
    report.append("=" * 50)
    
    return '\n'.join(report)


def count_items(text):
    """统计商品/服务项目数量"""
    lines = text.strip().split('\n')
    items = []
    current_class = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检测类别行
        if '第' in line and '类' in line:
            import re
            match = re.search(r'第(\d+)类', line)
            if match:
                current_class = int(match.group(1))
        
        # 检测项目行（以数字开头或"-"开头）
        if (line[0].isdigit() or line.startswith('-') or line.startswith('•')) and current_class:
            items.append((current_class, line))
    
    # 统计每类数量
    class_counts = {}
    for class_num, _ in items:
        class_counts[class_num] = class_counts.get(class_num, 0) + 1
    
    report = []
    report.append(f"商品/服务项目统计")
    report.append(f"总项目数：{len(items)}项")
    report.append(f"涉及类别：{len(class_counts)}类")
    report.append("\n各类项目数：")
    for class_num, count in sorted(class_counts.items()):
        status = "✓" if count <= 10 else "⚠️ 超出10项"
        report.append(f"  第{class_num}类：{count}项 {status}")
    
    return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(
        description='商标申请辅助工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询尼斯分类
  python trademark_helper.py --function classify --keyword 软件
  python trademark_helper.py --function classify --keyword 9
  
  # 检查商标图样
  python trademark_helper.py --function check-image --file logo.jpg
  
  # 计算费用
  python trademark_helper.py --function calculate-fee --classes 3
  python trademark_helper.py --function calculate-fee --classes 3 --items 8,12,10
  
  # 统计项目数量
  python trademark_helper.py --function count-items --text "第9类\\n1. 软件\\n2. 手机"
        """
    )
    
    parser.add_argument('-f', '--function',
                        choices=['classify', 'check-image', 'calculate-fee', 'count-items'],
                        required=True,
                        help='选择功能')
    parser.add_argument('-k', '--keyword',
                        help='搜索关键词（用于classify功能）')
    parser.add_argument('--file',
                        help='文件路径（用于check-image功能）')
    parser.add_argument('-c', '--classes', type=int,
                        help='类别数量（用于calculate-fee功能）')
    parser.add_argument('-i', '--items',
                        help='每类项目数，逗号分隔（用于calculate-fee功能）')
    parser.add_argument('-t', '--text',
                        help='文本内容（用于count-items功能）')
    parser.add_argument('--paper', action='store_true',
                        help='纸质申请（用于calculate-fee功能，默认电子申请）')
    
    args = parser.parse_args()
    
    if args.function == 'classify':
        if not args.keyword:
            print("错误：请提供搜索关键词，如：--keyword 软件")
            return
        
        results = search_classification(args.keyword)
        if results:
            print(f"关键词'{args.keyword}'的查询结果：\n")
            for class_num, description in results:
                print(f"第{class_num}类：{description}")
        else:
            print(f"未找到与'{args.keyword}'相关的类别")
            print("提示：可尝试使用更宽泛的关键词，如'电子'、'食品'、'服务'等")
    
    elif args.function == 'check-image':
        if not args.file:
            print("错误：请提供图片文件路径，如：--file logo.jpg")
            return
        
        if not Path(args.file).exists():
            print(f"错误：文件不存在：{args.file}")
            return
        
        print(check_image_requirements(args.file))
    
    elif args.function == 'calculate-fee':
        if not args.classes:
            print("错误：请提供类别数量，如：--classes 3")
            return
        
        items = None
        if args.items:
            try:
                items = [int(x) for x in args.items.split(',')]
            except ValueError:
                print("错误：项目数格式不正确，应为逗号分隔的数字，如：--items 8,12,10")
                return
        
        print(calculate_fee(args.classes, items, electronic=not args.paper))
    
    elif args.function == 'count-items':
        if not args.text:
            print("错误：请提供文本内容，如：--text '第9类\\n1. 软件'")
            return
        
        # 处理转义字符
        text = args.text.replace('\\n', '\n')
        print(count_items(text))


if __name__ == '__main__':
    main()
