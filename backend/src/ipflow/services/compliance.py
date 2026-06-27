"""专利与商标合规检查服务.

复用软著合规检查器的 ``CheckStatus`` / ``CheckCategory`` / ``ComplianceResult``
/ ``ComplianceReport`` 数据结构，为专利与商标申请材料提供独立的规则引擎。
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from ipflow.services.copyright.compliance_checker import (
    CheckCategory,
    CheckStatus,
    ComplianceReport,
    ComplianceResult,
)


def _summarize(results: List[ComplianceResult], project_id: UUID) -> ComplianceReport:
    """根据结果列表汇总为合规报告."""
    passed = sum(1 for r in results if r.status == CheckStatus.PASSED)
    warnings = sum(1 for r in results if r.status == CheckStatus.WARNING)
    failed = sum(1 for r in results if r.status == CheckStatus.FAILED)

    if failed > 0:
        overall_status = CheckStatus.FAILED
        can_export = False
    elif warnings > 0:
        overall_status = CheckStatus.WARNING
        can_export = True
    else:
        overall_status = CheckStatus.PASSED
        can_export = True

    return ComplianceReport(
        project_id=project_id,
        total_rules=len(results),
        passed=passed,
        warnings=warnings,
        failed=failed,
        results=results,
        overall_status=overall_status,
        can_export=can_export,
    )


class PatentComplianceChecker:
    """专利申请材料合规检查器."""

    def check(
        self,
        project_id: UUID,
        patent_info: Optional[Dict[str, Any]],
        description: Optional[Dict[str, Any]],
        claims: Optional[List[Dict[str, Any]]],
    ) -> ComplianceReport:
        """执行专利材料合规检查.

        Args:
            project_id: 项目ID
            patent_info: 专利基本信息（title/abstract/patent_type 等）
            description: 说明书各章节内容
            claims: 权利要求列表
        """
        results: List[ComplianceResult] = []
        results.extend(self._check_patent_info(patent_info))
        results.extend(self._check_description(description))
        results.extend(self._check_claims(claims))
        return _summarize(results, project_id)

    def _check_patent_info(
        self, info: Optional[Dict[str, Any]]
    ) -> List[ComplianceResult]:
        results: List[ComplianceResult] = []

        title = (info or {}).get("title", "")
        if title and len(str(title)) >= 2:
            results.append(
                ComplianceResult(
                    rule_id="P_INFO_001",
                    rule_name="发明名称",
                    category=CheckCategory.INFO,
                    status=CheckStatus.PASSED,
                    message="发明名称已填写",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="P_INFO_001",
                    rule_name="发明名称",
                    category=CheckCategory.INFO,
                    status=CheckStatus.FAILED,
                    message="发明名称不能为空",
                    suggestion="请填写专利/发明名称",
                )
            )

        abstract = (info or {}).get("abstract", "")
        if abstract and len(str(abstract)) >= 30:
            results.append(
                ComplianceResult(
                    rule_id="P_INFO_002",
                    rule_name="摘要",
                    category=CheckCategory.INFO,
                    status=CheckStatus.PASSED,
                    message=f"摘要共 {len(str(abstract))} 字",
                )
            )
        else:
            al = len(str(abstract)) if abstract else 0
            results.append(
                ComplianceResult(
                    rule_id="P_INFO_002",
                    rule_name="摘要",
                    category=CheckCategory.INFO,
                    status=CheckStatus.WARNING,
                    message=f"摘要仅 {al} 字，建议不少于30字（官方要求≤300字）",
                    suggestion="请补充摘要内容",
                )
            )

        patent_type = (info or {}).get("patent_type", "")
        if patent_type:
            results.append(
                ComplianceResult(
                    rule_id="P_INFO_003",
                    rule_name="专利类型",
                    category=CheckCategory.INFO,
                    status=CheckStatus.PASSED,
                    message=f"专利类型: {patent_type}",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="P_INFO_003",
                    rule_name="专利类型",
                    category=CheckCategory.INFO,
                    status=CheckStatus.WARNING,
                    message="未选择专利类型",
                    suggestion="请选择发明/实用新型/外观设计",
                )
            )

        return results

    def _check_description(
        self, description: Optional[Dict[str, Any]]
    ) -> List[ComplianceResult]:
        results: List[ComplianceResult] = []
        desc = description or {}

        # 说明书必备章节
        required_sections = {
            "technical_field": "技术领域",
            "background_art": "背景技术",
            "problem_solved": "要解决的技术问题",
            "technical_solution": "技术方案",
            "beneficial_effects": "有益效果",
        }
        if not desc:
            for field_name, label in required_sections.items():
                results.append(
                    ComplianceResult(
                        rule_id=f"P_DESC_{field_name.upper()}",
                        rule_name=f"说明书-{label}",
                        category=CheckCategory.MANUAL,
                        status=CheckStatus.FAILED,
                        message=f"缺少说明书章节: {label}",
                        suggestion=f"请填写{label}",
                    )
                )
            return results

        for field_name, label in required_sections.items():
            content = desc.get(field_name, "")
            rid = f"P_DESC_{field_name.upper()}"
            if content and len(str(content)) >= 10:
                results.append(
                    ComplianceResult(
                        rule_id=rid,
                        rule_name=f"说明书-{label}",
                        category=CheckCategory.MANUAL,
                        status=CheckStatus.PASSED,
                        message=f"{label}共 {len(str(content))} 字",
                    )
                )
            else:
                results.append(
                    ComplianceResult(
                        rule_id=rid,
                        rule_name=f"说明书-{label}",
                        category=CheckCategory.MANUAL,
                        status=CheckStatus.WARNING,
                        message=f"{label}内容过短或为空",
                        suggestion=f"请补充{label}内容",
                    )
                )

        implementation = desc.get("implementation", "")
        if implementation and len(str(implementation)) >= 20:
            results.append(
                ComplianceResult(
                    rule_id="P_DESC_IMPLEMENTATION",
                    rule_name="说明书-具体实施方式",
                    category=CheckCategory.MANUAL,
                    status=CheckStatus.PASSED,
                    message=f"具体实施方式共 {len(str(implementation))} 字",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="P_DESC_IMPLEMENTATION",
                    rule_name="说明书-具体实施方式",
                    category=CheckCategory.MANUAL,
                    status=CheckStatus.WARNING,
                    message="具体实施方式内容过短或为空",
                    suggestion="建议补充至少一个实施例",
                )
            )

        return results

    def _check_claims(
        self, claims: Optional[List[Dict[str, Any]]]
    ) -> List[ComplianceResult]:
        results: List[ComplianceResult] = []
        claims = claims or []

        if len(claims) == 0:
            results.append(
                ComplianceResult(
                    rule_id="P_CLAIM_001",
                    rule_name="权利要求",
                    category=CheckCategory.CODE,
                    status=CheckStatus.FAILED,
                    message="缺少权利要求",
                    suggestion="至少需要一项独立权利要求",
                )
            )
            return results

        results.append(
            ComplianceResult(
                rule_id="P_CLAIM_001",
                rule_name="权利要求",
                category=CheckCategory.CODE,
                status=CheckStatus.PASSED,
                message=f"共 {len(claims)} 项权利要求",
            )
        )

        has_independent = any(
            str(c.get("claim_type", "")).lower() in ("independent", "独立")
            or c.get("parent_claim_number") is None
            for c in claims
        )
        if has_independent:
            results.append(
                ComplianceResult(
                    rule_id="P_CLAIM_002",
                    rule_name="独立权利要求",
                    category=CheckCategory.CODE,
                    status=CheckStatus.PASSED,
                    message="存在独立权利要求",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="P_CLAIM_002",
                    rule_name="独立权利要求",
                    category=CheckCategory.CODE,
                    status=CheckStatus.FAILED,
                    message="未发现独立权利要求",
                    suggestion="至少需要一项独立权利要求",
                )
            )

        empty_content = [c for c in claims if not str(c.get("content", "")).strip()]
        if empty_content:
            results.append(
                ComplianceResult(
                    rule_id="P_CLAIM_003",
                    rule_name="权利要求内容",
                    category=CheckCategory.CODE,
                    status=CheckStatus.WARNING,
                    message=f"{len(empty_content)} 项权利要求内容为空",
                    suggestion="请补全权利要求内容",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="P_CLAIM_003",
                    rule_name="权利要求内容",
                    category=CheckCategory.CODE,
                    status=CheckStatus.PASSED,
                    message="所有权利要求均已填写内容",
                )
            )

        return results


class TrademarkComplianceChecker:
    """商标申请材料合规检查器."""

    def check(
        self,
        project_id: UUID,
        trademark_info: Optional[Dict[str, Any]],
        nice_classes: Optional[List[Dict[str, Any]]],
    ) -> ComplianceReport:
        """执行商标材料合规检查.

        Args:
            project_id: 项目ID
            trademark_info: 商标基本信息（trademark_name/trademark_type 等）
            nice_classes: 已选尼斯分类列表
        """
        results: List[ComplianceResult] = []
        results.extend(self._check_trademark_info(trademark_info))
        results.extend(self._check_nice_classes(nice_classes))
        return _summarize(results, project_id)

    def _check_trademark_info(
        self, info: Optional[Dict[str, Any]]
    ) -> List[ComplianceResult]:
        results: List[ComplianceResult] = []
        info = info or {}

        name = info.get("trademark_name", "")
        if name and len(str(name)) >= 1:
            results.append(
                ComplianceResult(
                    rule_id="T_INFO_001",
                    rule_name="商标名称",
                    category=CheckCategory.INFO,
                    status=CheckStatus.PASSED,
                    message=f"商标名称: {name}",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="T_INFO_001",
                    rule_name="商标名称",
                    category=CheckCategory.INFO,
                    status=CheckStatus.FAILED,
                    message="商标名称不能为空",
                    suggestion="请填写商标名称/文字",
                )
            )

        tm_type = info.get("trademark_type", "")
        if tm_type:
            results.append(
                ComplianceResult(
                    rule_id="T_INFO_002",
                    rule_name="商标类型",
                    category=CheckCategory.INFO,
                    status=CheckStatus.PASSED,
                    message=f"商标类型: {tm_type}",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="T_INFO_002",
                    rule_name="商标类型",
                    category=CheckCategory.INFO,
                    status=CheckStatus.WARNING,
                    message="未选择商标类型",
                    suggestion="请选择文字/图形/组合等商标类型",
                )
            )

        # 图形/组合/三维/颜色商标需要图样
        needs_image = str(tm_type) in ("device", "composite", "3d", "color", "graphic", "combined")
        has_image = bool(info.get("upload_id") or info.get("image_object_path"))
        if needs_image:
            if has_image:
                results.append(
                    ComplianceResult(
                        rule_id="T_INFO_003",
                        rule_name="商标图样",
                        category=CheckCategory.PROOF,
                        status=CheckStatus.PASSED,
                        message="已上传商标图样",
                    )
                )
            else:
                results.append(
                    ComplianceResult(
                        rule_id="T_INFO_003",
                        rule_name="商标图样",
                        category=CheckCategory.PROOF,
                        status=CheckStatus.FAILED,
                        message="该类型商标必须上传图样",
                        suggestion="请上传清晰的商标图样",
                    )
                )

        # 颜色商标需要颜色说明
        if str(tm_type) == "color":
            color_claim = info.get("color_claim", "")
            if color_claim:
                results.append(
                    ComplianceResult(
                        rule_id="T_INFO_004",
                        rule_name="颜色说明",
                        category=CheckCategory.INFO,
                        status=CheckStatus.PASSED,
                        message="已填写颜色说明",
                    )
                )
            else:
                results.append(
                    ComplianceResult(
                        rule_id="T_INFO_004",
                        rule_name="颜色说明",
                        category=CheckCategory.INFO,
                        status=CheckStatus.WARNING,
                        message="颜色商标建议填写颜色说明",
                        suggestion="请填写要求保护的颜色说明",
                    )
                )

        return results

    def _check_nice_classes(
        self, nice_classes: Optional[List[Dict[str, Any]]]
    ) -> List[ComplianceResult]:
        results: List[ComplianceResult] = []
        nice_classes = nice_classes or []

        if len(nice_classes) == 0:
            results.append(
                ComplianceResult(
                    rule_id="T_CLASS_001",
                    rule_name="尼斯分类",
                    category=CheckCategory.INFO,
                    status=CheckStatus.FAILED,
                    message="未选择任何尼斯分类",
                    suggestion="至少选择一个商品/服务类别",
                )
            )
            return results

        results.append(
            ComplianceResult(
                rule_id="T_CLASS_001",
                rule_name="尼斯分类",
                category=CheckCategory.INFO,
                status=CheckStatus.PASSED,
                message=f"已选择 {len(nice_classes)} 个类别",
            )
        )

        # 检查每个分类是否选择了具体商品/服务项目
        empty_classes = [
            nc for nc in nice_classes if not nc.get("goods_services")
        ]
        if empty_classes:
            results.append(
                ComplianceResult(
                    rule_id="T_CLASS_002",
                    rule_name="商品服务项目",
                    category=CheckCategory.INFO,
                    status=CheckStatus.WARNING,
                    message=f"{len(empty_classes)} 个类别未填写具体商品/服务项目",
                    suggestion="请为每个类别填写具体商品/服务",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    rule_id="T_CLASS_002",
                    rule_name="商品服务项目",
                    category=CheckCategory.INFO,
                    status=CheckStatus.PASSED,
                    message="所有类别均已填写商品/服务项目",
                )
            )

        return results
