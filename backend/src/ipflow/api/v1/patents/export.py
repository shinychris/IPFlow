"""专利导出 API.

提供专利申请材料导出功能。
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
    PatentData, PatentClaim, PatentDrawing, Project, 
    ProjectType, PatentExportConfig
)
from ipflow.models.user import User
from ipflow.api.deps import require_active_user
from ipflow.utils.enums import enum_value

router = APIRouter()


# =============================================================================
# 辅助函数
# =============================================================================

def generate_patent_text(patent_data: PatentData, claims: list) -> str:
    """生成专利说明书文本."""
    lines = []
    
    # 标题
    lines.append(f"专利名称：{patent_data.title}")
    lines.append("")
    
    # 摘要
    if patent_data.abstract:
        lines.append("摘要")
        lines.append("")
        lines.append(patent_data.abstract)
        if patent_data.abstract_figure_number:
            lines.append(f"摘要附图：{patent_data.abstract_figure_number}")
        lines.append("")
    
    # 技术领域
    if patent_data.technical_field:
        lines.append("技术领域")
        lines.append("")
        lines.append(patent_data.technical_field)
        lines.append("")
    
    # 背景技术
    if patent_data.background_art:
        lines.append("背景技术")
        lines.append("")
        lines.append(patent_data.background_art)
        lines.append("")
    
    # 发明内容
    if patent_data.invention_content:
        lines.append("发明内容")
        lines.append("")
        
        if patent_data.invention_content.get("problem_solved"):
            lines.append("要解决的技术问题：")
            lines.append(patent_data.invention_content["problem_solved"])
            lines.append("")
        
        if patent_data.invention_content.get("technical_solution"):
            lines.append("技术方案：")
            lines.append(patent_data.invention_content["technical_solution"])
            lines.append("")
        
        if patent_data.invention_content.get("beneficial_effects"):
            lines.append("有益效果：")
            lines.append(patent_data.invention_content["beneficial_effects"])
            lines.append("")
    
    # 附图说明（如果有附图）
    # 附图说明将在 drawings API 中处理
    
    # 具体实施方式
    if patent_data.implementation:
        lines.append("具体实施方式")
        lines.append("")
        lines.append(patent_data.implementation)
        lines.append("")
    
    # 权利要求书
    if claims:
        lines.append("权利要求书")
        lines.append("")
        for claim in claims:
            prefix = f"{claim.claim_number}. "
            if claim.claim_type == "dependent" and claim.parent_claim_number:
                prefix += f"根据权利要求{claim.parent_claim_number}所述的装置，"
            lines.append(f"{prefix}{claim.content}")
            lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# API 端点
# =============================================================================


@router.post("/export")
async def export_patent(
    project_id: UUID,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """导出专利申请材料包.
    
    生成包含所有申请材料的 ZIP 文件。
    """
    # 验证项目
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
            Project.project_type == ProjectType.PATENT,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取专利数据
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    if not patent_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先填写专利信息",
        )
    
    # 获取权利要求
    result = await db.execute(
        select(PatentClaim)
        .where(PatentClaim.patent_data_id == patent_data.id)
        .order_by(PatentClaim.claim_number)
    )
    claims = result.scalars().all()
    
    # 生成 ZIP 文件
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. 专利说明书
        description_text = generate_patent_text(patent_data, claims)
        zf.writestr(
            f"01_说明书_{patent_data.title}.txt",
            description_text.encode('utf-8')
        )
        
        # 2. 权利要求书（单独文件）
        if claims:
            claims_text = "权利要求书\n\n"
            for claim in claims:
                prefix = f"{claim.claim_number}. "
                if claim.claim_type == "dependent" and claim.parent_claim_number:
                    prefix += f"根据权利要求{claim.parent_claim_number}所述的装置，"
                claims_text += f"{prefix}{claim.content}\n\n"
            
            zf.writestr(
                f"02_权利要求书_{patent_data.title}.txt",
                claims_text.encode('utf-8')
            )
        
        # 3. 摘要
        if patent_data.abstract:
            abstract_text = f"摘要\n\n{patent_data.abstract}\n"
            if patent_data.abstract_figure_number:
                abstract_text += f"摘要附图：{patent_data.abstract_figure_number}\n"
            
            zf.writestr(
                f"03_摘要_{patent_data.title}.txt",
                abstract_text.encode('utf-8')
            )
        
        # 4. 材料清单
        manifest = f"""专利申请材料清单
====================

专利名称：{patent_data.title}
专利类型：{enum_value(patent_data.patent_type)}
生成时间：{datetime.utcnow().isoformat()}

文件列表：
1. 说明书
2. 权利要求书（{len(claims)} 项）
3. 摘要
4. 摘要附图（如有）
5. 附图（{patent_data.drawings_count} 张）

注意：
- 请确保所有材料完整后再提交
- 附图需要单独提供高质量图片
- CPC 客户端提交时请按顺序上传
"""
        zf.writestr("00_材料清单.txt", manifest.encode('utf-8'))
    
    zip_buffer.seek(0)
    
    # 更新项目状态
    from ipflow.models import ProjectStatus
    project.status = ProjectStatus.PENDING_SUBMIT
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    # 返回文件流
    filename = f"专利申请包_{patent_data.title}_{datetime.now().strftime('%Y%m%d')}.zip"
    
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
            Project.project_type == ProjectType.PATENT,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    
    # 获取专利数据
    result = await db.execute(
        select(PatentData).where(PatentData.project_id == project_id)
    )
    patent_data = result.scalar_one_or_none()
    
    # 获取权利要求
    claims = []
    if patent_data:
        result = await db.execute(
            select(PatentClaim)
            .where(PatentClaim.patent_data_id == patent_data.id)
            .order_by(PatentClaim.claim_number)
        )
        claims = result.scalars().all()
    
    # 检查内容完整性
    checks = {
        "has_patent_info": patent_data is not None,
        "has_title": patent_data and bool(patent_data.title),
        "has_abstract": patent_data and bool(patent_data.abstract),
        "has_technical_field": patent_data and bool(patent_data.technical_field),
        "has_background_art": patent_data and bool(patent_data.background_art),
        "has_invention_content": patent_data and bool(patent_data.invention_content),
        "has_implementation": patent_data and bool(patent_data.implementation),
        "has_claims": len(claims) > 0,
        "has_drawings": patent_data and patent_data.drawings_count > 0,
    }
    
    all_ready = all([
        checks["has_patent_info"],
        checks["has_title"],
        checks["has_abstract"],
        checks["has_claims"],
    ])
    
    return {
        "patent_info": {
            "has_data": patent_data is not None,
            "title": patent_data.title if patent_data else None,
            "patent_type": enum_value(patent_data.patent_type) if patent_data else None,
        },
        "claims": {
            "count": len(claims),
            "independent_count": sum(1 for c in claims if c.claim_type == "independent"),
            "dependent_count": sum(1 for c in claims if c.claim_type == "dependent"),
        },
        "drawings": {
            "count": patent_data.drawings_count if patent_data else 0,
        },
        "files_in_package": [
            "01_说明书.txt",
            "02_权利要求书.txt",
            "03_摘要.txt",
            "00_材料清单.txt",
        ],
        "completeness": {
            "checks": checks,
            "all_ready": all_ready,
            "missing_items": [k for k, v in checks.items() if not v],
        },
    }
