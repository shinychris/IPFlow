"""商标导出 API.

提供商标申请材料导出功能。
"""

from datetime import datetime
from uuid import UUID
from io import BytesIO
import zipfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models import (
    TrademarkData, TrademarkNiceClass, NiceClassification,
    Project, ProjectType, TrademarkExportConfig
)
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.utils.enums import enum_value

router = APIRouter()


# =============================================================================
# 辅助函数
# =============================================================================

def generate_trademark_text(trademark_data: TrademarkData, nice_classes: list) -> str:
    """生成商标注册申请书文本."""
    lines = []
    
    # 标题
    lines.append("商标注册申请书")
    lines.append("")
    
    # 商标信息
    lines.append("一、商标信息")
    lines.append(f"商标类型：{enum_value(trademark_data.trademark_type)}")
    if trademark_data.trademark_name:
        lines.append(f"商标名称/文字：{trademark_data.trademark_name}")
    if trademark_data.description:
        lines.append(f"商标描述：{trademark_data.description}")
    if trademark_data.design_description:
        lines.append(f"设计说明：{trademark_data.design_description}")
    if trademark_data.color_claim:
        lines.append(f"颜色说明：{trademark_data.color_claim}")
    if trademark_data.special_notes:
        lines.append(f"特殊说明：{trademark_data.special_notes}")
    lines.append("")
    
    # 商品/服务类别
    lines.append("二、商品/服务类别")
    if nice_classes:
        for item in nice_classes:
            lines.append(f"第 {item['class_number']} 类 - {item['class_name']}")
            if item['goods_services']:
                lines.append("商品/服务项目：")
                for service in item['goods_services']:
                    lines.append(f"  - {service}")
            lines.append("")
    else:
        lines.append("（未选择任何类别）")
    lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# API 端点
# =============================================================================


@router.post("/export")
async def export_trademark(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """导出商标申请材料包.
    
    生成包含所有申请材料的 ZIP 文件。
    """
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取商标数据
    result = await db.execute(
        select(TrademarkData).where(TrademarkData.project_id == project_id)
    )
    trademark_data = result.scalar_one_or_none()
    
    if not trademark_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先填写商标信息",
        )
    
    # 获取已选择的尼斯分类
    result = await db.execute(
        select(TrademarkNiceClass, NiceClassification)
        .join(NiceClassification, TrademarkNiceClass.nice_class_id == NiceClassification.id)
        .where(TrademarkNiceClass.trademark_data_id == trademark_data.id)
        .order_by(NiceClassification.class_number)
    )
    rows = result.all()
    
    nice_classes = [
        {
            "class_number": row.NiceClassification.class_number,
            "class_name": row.NiceClassification.class_name,
            "goods_services": row.TrademarkNiceClass.goods_services,
        }
        for row in rows
    ]
    
    # 生成 ZIP 文件
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. 商标注册申请书
        application_text = generate_trademark_text(trademark_data, nice_classes)
        trademark_name = trademark_data.trademark_name or "未命名商标"
        zf.writestr(
            f"01_商标注册申请书_{trademark_name}.txt",
            application_text.encode('utf-8')
        )
        
        # 2. 商品/服务分类清单
        if nice_classes:
            classes_text = "商品/服务分类清单\n====================\n\n"
            for item in nice_classes:
                classes_text += f"第 {item['class_number']} 类 - {item['class_name']}\n"
                if item['goods_services']:
                    classes_text += "商品/服务项目：\n"
                    for service in item['goods_services']:
                        classes_text += f"  - {service}\n"
                classes_text += "\n"
            
            zf.writestr(
                "02_商品服务分类清单.txt",
                classes_text.encode('utf-8')
            )
        
        # 3. 材料清单
        manifest = f"""商标申请材料清单
====================

商标名称：{trademark_data.trademark_name or "（未命名）"}
商标类型：{enum_value(trademark_data.trademark_type)}
申请类别：{len(nice_classes)} 个类别
生成时间：{datetime.utcnow().isoformat()}

文件列表：
1. 商标注册申请书
2. 商品/服务分类清单
3. 商标图样（需单独提供）
4. 申请人身份证明文件
5. 代理委托书（如委托代理）

注意：
- 请确保所有材料完整后再提交
- 商标图样需要单独提供高质量图片
- 网上申报时请按系统要求上传
- 多个类别需要分别缴纳规费
"""
        zf.writestr("00_材料清单.txt", manifest.encode('utf-8'))
    
    zip_buffer.seek(0)
    
    # 更新项目状态
    from ipflow.models import ProjectStatus
    project.status = ProjectStatus.PENDING_SUBMIT
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    # 返回文件流
    filename = f"商标申请包_{trademark_data.trademark_name or '未命名'}_{datetime.now().strftime('%Y%m%d')}.zip"
    
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(zip_buffer.getbuffer().nbytes),
        },
    )


@router.get("/export/preview", response_model=dict)
async def preview_export(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """预览导出内容.
    
    返回导出包的预览信息，不生成文件。
    """
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.TRADEMARK,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取商标数据
    result = await db.execute(
        select(TrademarkData).where(TrademarkData.project_id == project_id)
    )
    trademark_data = result.scalar_one_or_none()
    
    # 获取已选择的尼斯分类
    nice_classes = []
    if trademark_data:
        result = await db.execute(
            select(TrademarkNiceClass, NiceClassification)
            .join(NiceClassification, TrademarkNiceClass.nice_class_id == NiceClassification.id)
            .where(TrademarkNiceClass.trademark_data_id == trademark_data.id)
            .order_by(NiceClassification.class_number)
        )
        rows = result.all()
        nice_classes = [
            {
                "class_number": row.NiceClassification.class_number,
                "class_name": row.NiceClassification.class_name,
                "goods_services": row.TrademarkNiceClass.goods_services,
            }
            for row in rows
        ]
    
    # 检查内容完整性
    checks = {
        "has_trademark_info": trademark_data is not None,
        "has_trademark_type": trademark_data and trademark_data.trademark_type is not None,
        "has_trademark_name": trademark_data and bool(trademark_data.trademark_name),
        "has_upload": trademark_data and trademark_data.upload_id is not None,
        "has_nice_classes": len(nice_classes) > 0,
    }
    
    all_ready = all([
        checks["has_trademark_info"],
        checks["has_trademark_type"],
        checks["has_nice_classes"],
    ])
    
    return {
        "trademark_info": {
            "has_data": trademark_data is not None,
            "trademark_name": trademark_data.trademark_name if trademark_data else None,
            "trademark_type": enum_value(trademark_data.trademark_type) if trademark_data else None,
        },
        "nice_classes": {
            "count": len(nice_classes),
            "items": nice_classes,
        },
        "files_in_package": [
            "01_商标注册申请书.txt",
            "02_商品服务分类清单.txt",
            "00_材料清单.txt",
        ],
        "completeness": {
            "checks": checks,
            "all_ready": all_ready,
            "missing_items": [k for k, v in checks.items() if not v],
        },
    }
