"""尼斯分类（Nice Classification）种子数据.

尼斯协定第 11 版（NCL11-2025）共 45 个类别：1-34 为商品类，35-45 为服务类。
本模块在应用启动时（开发环境）按需填充 ``nice_classification`` 表，保证商标
模块的尼斯分类查询功能开箱可用。

数据为官方类别标题的标准简述，满足商标分类选择与合规检查需要。
"""

from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ipflow.models.trademark import NiceClassification

# (类别号, 中文名, 英文名, 说明)
NICE_CLASSES: list[tuple[int, str, str, str]] = [
    (1, "化学原料", "Chemicals", "用于工业、科学、农业、园艺和林业的化学品。"),
    (2, "颜料油漆", "Paints", "颜料、清漆、漆；防锈剂和木材防腐剂；着色剂。"),
    (3, "日化用品", "Cosmetics and Cleaning", "洗衣用漂白剂及其他清洁制剂；肥皂、香水、精油、化妆品。"),
    (4, "燃料油脂", "Lubricants and Fuels", "工业用油和油脂；润滑剂；燃料和照明材料。"),
    (5, "医药", "Pharmaceuticals", "药品和医用制剂；医用营养品；兽药用制剂。"),
    (6, "金属材料", "Metals", "普通金属及其合金；金属建筑材料；金属小五金器具。"),
    (7, "机械设备", "Machinery", "机器和机床；马达和引擎；机器联结器和传动机件。"),
    (8, "手工器械", "Hand Tools", "手工具和器具；刀、叉、匙；剃刀。"),
    (9, "科学仪器", "Scientific Instruments", "科学、测量、摄影、电影、光学、信号及计算设备；软件。"),
    (10, "医疗器械", "Medical Instruments", "医疗仪器、器械及用品；牙科、兽医用仪器及用品。"),
    (11, "灯具空调", "Environmental Control", "照明、加热、蒸汽、烹调、冷藏、干燥、通风、供水设备。"),
    (12, "运输工具", "Vehicles", "车辆、陆空海水的运载装置。"),
    (13, "军火烟火", "Firearms", "火器、军火和弹药；爆炸物；烟火。"),
    (14, "珠宝钟表", "Jewelry", "贵金属及其合金、珠宝、首饰、宝石；钟表和计时仪器。"),
    (15, "乐器", "Musical Instruments", "乐器。"),
    (16, "办公用品", "Paper Goods", "纸、纸板及纸制品；印刷品；书籍装订材料；文具。"),
    (17, "橡胶制品", "Rubber Goods", "未加工和半加工的橡胶、古塔胶、树胶及制品；绝缘材料。"),
    (18, "皮革皮具", "Leather Goods", "皮革和人造皮革及制品；毛皮；箱包、雨伞、手杖。"),
    (19, "建筑材料", "Building Materials", "非金属建筑材料；建筑用非金属刚性管；沥青、柏油。"),
    (20, "家具", "Furniture", "家具、镜子、相框；木、软木、苇、藤、柳条制品。"),
    (21, "家庭用具", "Household Glassware", "家庭或厨房用器具和容器；梳子、海绵、刷子；玻璃、瓷、陶器。"),
    (22, "绳网袋篷", "Cordage and Ropes", "绳、线、网、帐篷、遮篷、防水布、帆；衬垫和填充材料。"),
    (23, "纱线丝", "Yarns and Threads", "纺织用纱和线。"),
    (24, "布料床单", "Fabrics", "织物和织物替代品；床罩；桌布；纺织品。"),
    (25, "服装鞋帽", "Clothing", "服装、鞋、帽。"),
    (26, "花边拉链", "Lace and Embellishments", "花边、刺绣、饰带和编带；纽扣、钩扣、饰针、拉链。"),
    (27, "地毯席垫", "Carpets and Mats", "地毯、地席、席垫、油毡及其他铺地板用品；墙帷。"),
    (28, "健身器材", "Games and Toys", "游戏器具和玩具；体育和运动用品；圣诞装饰。"),
    (29, "肉蛋奶油", "Meat and Processured Foods", "肉、鱼、家禽和野味；肉汁；腌渍、冷冻、干制蔬果；蛋、奶、油。"),
    (30, "方便食品", "Staple Foods", "咖啡、茶、可可、糖、米、食用淀粉、面粉、面食；面包、糕点、糖果。"),
    (31, "饲料种籽", "Natural Agricultural", "农业、园艺、林业产品；活动物；新鲜水果和蔬菜；种籽。"),
    (32, "啤酒饮料", "Beers and Beverages", "啤酒、矿泉水和汽水及其他不含酒精的饮料；果汁；糖浆。"),
    (33, "酒", "Alcoholic Beverages", "含酒精的饮料（啤酒除外）。"),
    (34, "烟草烟具", "Tobacco", "烟草、烟具、火柴。"),
    (35, "广告销售", "Advertising and Business", "广告、商业经营、商业管理和办公事务。"),
    (36, "金融物管", "Financial and Real Estate", "保险、金融、货币事务、不动产事务。"),
    (37, "建筑修理", "Construction and Repair", "房屋建筑、修理、安装服务。"),
    (38, "通讯电信", "Telecommunications", "电信。"),
    (39, "运输旅行", "Transportation", "运输和旅行安排；商品包装和贮藏。"),
    (40, "材料加工", "Material Treatment", "材料处理。"),
    (41, "教育娱乐", "Education and Entertainment", "教育、培训、娱乐、文体活动。"),
    (42, "网站服务", "Scientific and IT", "科学技术服务和相关研究；工业分析和研究；计算机硬件软件设计与开发。"),
    (43, "餐饮住宿", "Food and Drink Services", "提供食物和饮料服务；临时住宿。"),
    (44, "医疗园艺", "Medical and Beauty", "医疗服务、兽医服务、人或动物的卫生美容服务；农业园艺林业服务。"),
    (45, "社会服务", "Legal and Social", "法律服务、为保护财产和人身安全的服务；由他人提供的满足个人需要的社交服务。"),
]


async def seed_nice_classifications(session: AsyncSession) -> int:
    """若尼斯分类表为空，则填充 45 个类别。

    Args:
        session: 数据库会话

    Returns:
        本次新增的类别数（表已存在数据则返回 0）
    """
    result = await session.execute(select(NiceClassification).limit(1))
    if result.scalars().first() is not None:
        return 0

    objs = [
        NiceClassification(
            class_number=num,
            class_name=name_cn,
            class_name_en=name_en,
            description=desc,
            is_active=True,
        )
        for num, name_cn, name_en, desc in NICE_CLASSES
    ]
    session.add_all(objs)
    await session.commit()
    return len(objs)
