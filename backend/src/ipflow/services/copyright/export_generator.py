"""导出包生成服务.

生成软著申请材料的导出包。
"""

import io
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID


@dataclass
class ExportConfig:
    """导出配置."""
    
    software_name: str
    version: str
    applicant_name: str
    completion_date: str
    first_publication_date: Optional[str] = None


@dataclass
class ExportResult:
    """导出结果."""
    
    file_name: str
    file_size: int
    content: bytes
    generated_at: datetime


class ExportGenerator:
    """导出包生成器.
    
    生成软著申请材料的 ZIP 导出包。
    """
    
    def generate_export_package(
        self,
        config: ExportConfig,
        software_info: dict,
        code_pages: List[dict],
        manual: Optional[dict],
        output_format: str = "text",
    ) -> ExportResult:
        """生成导出包.
        
        Args:
            config: 导出配置
            software_info: 软件信息
            code_pages: 代码页数据
            manual: 说明书数据
            output_format: 输出格式（text/pdf）
            
        Returns:
            导出结果
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. 软件信息
            self._add_software_info(zf, config, software_info)
            
            # 2. 源代码（分页格式）
            self._add_source_code(zf, config, code_pages)
            
            # 3. 操作说明书
            if manual:
                self._add_manual(zf, config, manual)
            
            # 4. 材料清单
            self._add_materials_list(zf, config, software_info, code_pages, manual)
            
            # 5. 打印指南
            self._add_printing_guide(zf, config)
            
            # 6. 网报对照表
            self._add_online_submission_guide(zf, config, software_info)
        
        zip_buffer.seek(0)
        content = zip_buffer.read()
        
        # 生成文件名
        safe_name = self._sanitize_filename(config.software_name)
        file_name = f"软著申请_{safe_name}_{config.version}_{datetime.now().strftime('%Y%m%d')}.zip"
        
        return ExportResult(
            file_name=file_name,
            file_size=len(content),
            content=content,
            generated_at=datetime.utcnow(),
        )
    
    def _sanitize_filename(self, name: str) -> str:
        """清理文件名."""
        import re
        # 移除非法字符
        safe = re.sub(r'[\\/*?:"<>|]', "", name)
        # 限制长度
        return safe[:50]
    
    def _add_software_info(
        self,
        zf: zipfile.ZipFile,
        config: ExportConfig,
        software_info: dict,
    ) -> None:
        """添加软件信息文件."""
        content = f"""软件著作权申请 - 软件信息
================================

软件全称：{config.software_name}
软件简称：{software_info.get('software_short_name', '无')}
版本号：{config.version}

开发信息
--------
开发语言：{software_info.get('development_language', '')}
开发环境：{software_info.get('development_environment', '')}
运行环境：{software_info.get('runtime_environment', '')}
代码行数：{software_info.get('code_line_count', 0)} 行

完成日期：{config.completion_date}
首次发表日期：{config.first_publication_date or '未发表'}

功能描述
--------
{software_info.get('functional_description', '')}

技术特点
--------
{software_info.get('technical_features', '')}

面向领域：{software_info.get('target_domain', '')}

生成时间：{datetime.now().isoformat()}
"""
        zf.writestr("01_软件信息.txt", content.encode('utf-8'))
    
    def _add_source_code(
        self,
        zf: zipfile.ZipFile,
        config: ExportConfig,
        code_pages: List[dict],
    ) -> None:
        """添加源代码文件."""
        if not code_pages:
            zf.writestr("02_源代码_鉴别材料.txt", "未上传源代码")
            return
        
        # 将所有页面合并为一个文件
        parts = []
        parts.append(f"{config.software_name} {config.version}")
        parts.append("源代码鉴别材料（前30页+后30页）")
        parts.append("=" * 80)
        parts.append("")
        
        for page in code_pages:
            parts.append(page.get('content', ''))
            parts.append("")  # 页面间隔
        
        content = "\\n".join(parts)
        zf.writestr("02_源代码_鉴别材料.txt", content.encode('utf-8'))
    
    def _add_manual(
        self,
        zf: zipfile.ZipFile,
        config: ExportConfig,
        manual: dict,
    ) -> None:
        """添加操作说明书."""
        title = manual.get('title', '操作说明书')
        content_html = manual.get('content_html', '')
        
        # 简单移除 HTML 标签
        import re
        text_content = re.sub(r'<[^>]+>', '', content_html)
        
        full_content = f"""{config.software_name} {config.version}
{title}
{'=' * 80}

{text_content}
"""
        zf.writestr("03_操作说明书.txt", full_content.encode('utf-8'))
    
    def _add_materials_list(
        self,
        zf: zipfile.ZipFile,
        config: ExportConfig,
        software_info: dict,
        code_pages: List[dict],
        manual: Optional[dict],
    ) -> None:
        """添加材料清单."""
        items = [
            "【必须材料】",
            "□ 软件著作权登记申请表（需在线填写后打印）",
            "□ 源代码鉴别材料（前30页+后30页）",
            "□ 操作说明书（不少于15页）",
            "",
            "【身份证明】",
            "□ 申请人身份证明复印件（企业：营业执照，个人：身份证）",
            "",
        ]
        
        # 根据项目情况添加可选材料
        if software_info.get('development_method') in ['cooperative', 'commission']:
            items.extend([
                "【权利归属证明】",
                "□ 合作开发协议 / 委托开发协议",
                "",
            ])
        
        items.extend([
            "材料清单生成时间：" + datetime.now().isoformat(),
            "",
            "注意事项：",
            "1. 所有材料需打印后加盖公章（企业）或签字（个人）",
            "2. 源代码需连续打印，不得有空行或跳页",
            "3. 操作说明书需包含软件界面截图",
            "4. 如有多份代码包，只需提交一份的源代码",
        ])
        
        content = "\\n".join(items)
        zf.writestr("04_材料清单.txt", content.encode('utf-8'))
    
    def _add_printing_guide(
        self,
        zf: zipfile.ZipFile,
        config: ExportConfig,
    ) -> None:
        """添加打印指南."""
        content = f"""软著申请材料打印指南
====================

一、纸张要求
-----------
- 纸张规格：A4 纸张
- 打印方式：单面打印
- 纸张质量：建议使用 80g 纸张

二、源代码打印要求
---------------
- 页眉格式：{config.software_name} {config.version} 第X页
- 行号格式：5位对齐（00001, 00002...）
- 每页行数：50行
- 字体：小五号或等宽字体
- 页边距：上下 2.54cm，左右 3.17cm

三、说明书打印要求
---------------
- 页数：不少于15页
- 字体：正文宋体小四
- 行距：1.5倍行距
- 页边距：上下 2.54cm，左右 3.17cm

四、装订要求
-----------
- 无需装订，按顺序排列
- 每份材料用回形针或夹子固定
- 提交时按清单顺序放置

五、提交份数
-----------
- 纸质材料：1份
- 电子版：通过版权中心网站提交

生成时间：{datetime.now().isoformat()}
"""
        zf.writestr("05_打印指南.txt", content.encode('utf-8'))
    
    def _add_online_submission_guide(
        self,
        zf: zipfile.ZipFile,
        config: ExportConfig,
        software_info: dict,
    ) -> None:
        """添加网报对照表."""
        content = f"""网报字段对照表
==============

本文件用于在线填写软著申请时的字段对照。

【软件信息】
-----------
软件全称：{config.software_name}
软件简称：{software_info.get('software_short_name', '')}
版本号：{config.version}
开发完成日期：{config.completion_date}
首次发表日期：{config.first_publication_date or '未发表'}

【技术信息】
-----------
开发语言：{software_info.get('development_language', '')}
适用行业：{software_info.get('target_domain', '')}
软件用途：{software_info.get('functional_description', '')[:200]}...

【著作权人信息】
--------------
姓名/名称：{config.applicant_name}
类别：根据申请人类型选择（企业/个人）

【材料上传】
-----------
1. 源代码鉴别材料 → 上传 02_源代码_鉴别材料.txt
2. 操作说明书 → 上传 03_操作说明书.txt
3. 身份证明 → 扫描上传
4. 其他证明材料 → 如有则上传

【注意事项】
-----------
1. 在线填写时需与纸质材料一致
2. 所有日期格式：YYYY-MM-DD
3. 上传文件大小限制：通常为 10MB
4. 建议提前准备好所有扫描件

生成时间：{datetime.now().isoformat()}
"""
        zf.writestr("06_网报对照表.txt", content.encode('utf-8'))
