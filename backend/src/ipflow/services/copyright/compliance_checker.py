"""合规检查服务.

提供软著申请材料的合规性检查。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID


class CheckStatus(str, Enum):
    """检查状态."""
    
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckCategory(str, Enum):
    """检查类别."""
    
    INFO = "info"      # 软件信息
    CODE = "code"      # 代码材料
    MANUAL = "manual"  # 说明书
    PROOF = "proof"    # 证明材料


@dataclass
class ComplianceRule:
    """合规规则."""
    
    id: str
    name: str
    category: CheckCategory
    description: str
    severity: str  # error, warning, info


@dataclass
class ComplianceResult:
    """合规检查结果."""
    
    rule_id: str
    rule_name: str
    category: CheckCategory
    status: CheckStatus
    message: str
    suggestion: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    """合规检查报告."""
    
    project_id: UUID
    total_rules: int
    passed: int
    warnings: int
    failed: int
    results: List[ComplianceResult]
    overall_status: CheckStatus
    can_export: bool


class ComplianceChecker:
    """合规检查器.
    
    检查软著申请材料的完整性和合规性。
    """
    
    # 合规规则定义
    RULES: List[ComplianceRule] = [
        # 软件信息规则
        ComplianceRule(
            id="INFO_001",
            name="软件全称",
            category=CheckCategory.INFO,
            description="软件全称不能为空",
            severity="error",
        ),
        ComplianceRule(
            id="INFO_002",
            name="版本号",
            category=CheckCategory.INFO,
            description="版本号不能为空",
            severity="error",
        ),
        ComplianceRule(
            id="INFO_003",
            name="开发语言",
            category=CheckCategory.INFO,
            description="开发语言不能为空",
            severity="error",
        ),
        ComplianceRule(
            id="INFO_004",
            name="功能描述",
            category=CheckCategory.INFO,
            description="功能描述应不少于50字",
            severity="warning",
        ),
        ComplianceRule(
            id="INFO_005",
            name="技术特点",
            category=CheckCategory.INFO,
            description="技术特点应不少于20字",
            severity="warning",
        ),
        
        # 代码材料规则
        ComplianceRule(
            id="CODE_001",
            name="代码总行数",
            category=CheckCategory.CODE,
            description="代码总行数应不少于3000行",
            severity="error",
        ),
        ComplianceRule(
            id="CODE_002",
            name="代码文件数",
            category=CheckCategory.CODE,
            description="代码文件数应不少于5个",
            severity="warning",
        ),
        ComplianceRule(
            id="CODE_003",
            name="代码页数",
            category=CheckCategory.CODE,
            description="代码材料应为60页（前30+后30）",
            severity="warning",
        ),
        
        # 说明书规则
        ComplianceRule(
            id="MANUAL_001",
            name="说明书标题",
            category=CheckCategory.MANUAL,
            description="说明书标题不能为空",
            severity="error",
        ),
        ComplianceRule(
            id="MANUAL_002",
            name="说明书页数",
            category=CheckCategory.MANUAL,
            description="说明书应不少于15页",
            severity="error",
        ),
        ComplianceRule(
            id="MANUAL_003",
            name="说明书字数",
            category=CheckCategory.MANUAL,
            description="说明书应不少于3000字",
            severity="warning",
        ),
        ComplianceRule(
            id="MANUAL_004",
            name="目录",
            category=CheckCategory.MANUAL,
            description="建议添加目录",
            severity="warning",
        ),
        ComplianceRule(
            id="MANUAL_005",
            name="章节结构",
            category=CheckCategory.MANUAL,
            description="建议添加规范章节结构",
            severity="warning",
        ),
        
        # 证明材料规则（预留）
        ComplianceRule(
            id="PROOF_001",
            name="身份证明",
            category=CheckCategory.PROOF,
            description="需要提供申请人身份证明",
            severity="error",
        ),
        ComplianceRule(
            id="PROOF_002",
            name="权利归属证明",
            category=CheckCategory.PROOF,
            description="合作开发需要提供权利归属证明",
            severity="warning",
        ),
    ]
    
    def __init__(self):
        """初始化合规检查器."""
        self.rules_map = {rule.id: rule for rule in self.RULES}
    
    def check(
        self,
        project_id: UUID,
        software_info: Optional[Dict[str, Any]],
        code_bundle: Optional[Dict[str, Any]],
        manual: Optional[Dict[str, Any]],
        proofs: Optional[List[Dict[str, Any]]] = None,
    ) -> ComplianceReport:
        """执行合规检查.
        
        Args:
            project_id: 项目ID
            software_info: 软件信息
            code_bundle: 代码包信息
            manual: 说明书信息
            proofs: 证明材料列表
            
        Returns:
            合规检查报告
        """
        results: List[ComplianceResult] = []
        
        # 检查软件信息
        if software_info:
            results.extend(self._check_software_info(software_info))
        else:
            # 没有软件信息，所有相关检查失败
            for rule in self.RULES:
                if rule.category == CheckCategory.INFO:
                    results.append(ComplianceResult(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        category=rule.category,
                        status=CheckStatus.FAILED,
                        message=f"缺少软件信息: {rule.description}",
                        suggestion="请先填写软件信息",
                    ))
        
        # 检查代码
        if code_bundle:
            results.extend(self._check_code(code_bundle))
        else:
            results.append(ComplianceResult(
                rule_id="CODE_001",
                rule_name="代码材料",
                category=CheckCategory.CODE,
                status=CheckStatus.FAILED,
                message="缺少代码材料",
                suggestion="请上传源代码 ZIP 文件",
            ))
        
        # 检查说明书
        if manual:
            results.extend(self._check_manual(manual))
        else:
            results.append(ComplianceResult(
                rule_id="MANUAL_001",
                rule_name="操作说明书",
                category=CheckCategory.MANUAL,
                status=CheckStatus.FAILED,
                message="缺少操作说明书",
                suggestion="请创建操作说明书",
            ))
        
        # 计算统计
        passed = sum(1 for r in results if r.status == CheckStatus.PASSED)
        warnings = sum(1 for r in results if r.status == CheckStatus.WARNING)
        failed = sum(1 for r in results if r.status == CheckStatus.FAILED)
        
        # 判断整体状态
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
    
    def _check_software_info(
        self,
        info: Dict[str, Any],
    ) -> List[ComplianceResult]:
        """检查软件信息."""
        results = []
        
        # 检查软件全称
        full_name = info.get("software_full_name", "")
        if full_name and len(full_name) >= 2:
            results.append(ComplianceResult(
                rule_id="INFO_001",
                rule_name="软件全称",
                category=CheckCategory.INFO,
                status=CheckStatus.PASSED,
                message="软件全称已填写",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="INFO_001",
                rule_name="软件全称",
                category=CheckCategory.INFO,
                status=CheckStatus.FAILED,
                message="软件全称不能为空",
                suggestion="请填写软件全称",
            ))
        
        # 检查版本号
        version = info.get("version_number", "")
        if version:
            results.append(ComplianceResult(
                rule_id="INFO_002",
                rule_name="版本号",
                category=CheckCategory.INFO,
                status=CheckStatus.PASSED,
                message="版本号已填写",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="INFO_002",
                rule_name="版本号",
                category=CheckCategory.INFO,
                status=CheckStatus.FAILED,
                message="版本号不能为空",
                suggestion="请填写版本号",
            ))
        
        # 检查开发语言
        language = info.get("development_language", "")
        if language:
            results.append(ComplianceResult(
                rule_id="INFO_003",
                rule_name="开发语言",
                category=CheckCategory.INFO,
                status=CheckStatus.PASSED,
                message="开发语言已填写",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="INFO_003",
                rule_name="开发语言",
                category=CheckCategory.INFO,
                status=CheckStatus.FAILED,
                message="开发语言不能为空",
                suggestion="请填写开发语言",
            ))
        
        # 检查功能描述
        desc = info.get("functional_description", "")
        if desc and len(desc) >= 50:
            results.append(ComplianceResult(
                rule_id="INFO_004",
                rule_name="功能描述",
                category=CheckCategory.INFO,
                status=CheckStatus.PASSED,
                message=f"功能描述共 {len(desc)} 字",
            ))
        else:
            desc_len = len(desc) if desc else 0
            results.append(ComplianceResult(
                rule_id="INFO_004",
                rule_name="功能描述",
                category=CheckCategory.INFO,
                status=CheckStatus.WARNING,
                message=f"功能描述仅 {desc_len} 字，建议不少于50字",
                suggestion="请补充功能描述",
            ))
        
        # 检查技术特点
        features = info.get("technical_features", "")
        if features and len(features) >= 20:
            results.append(ComplianceResult(
                rule_id="INFO_005",
                rule_name="技术特点",
                category=CheckCategory.INFO,
                status=CheckStatus.PASSED,
                message=f"技术特点共 {len(features)} 字",
            ))
        else:
            features_len = len(features) if features else 0
            results.append(ComplianceResult(
                rule_id="INFO_005",
                rule_name="技术特点",
                category=CheckCategory.INFO,
                status=CheckStatus.WARNING,
                message=f"技术特点仅 {features_len} 字，建议不少于20字",
                suggestion="请补充技术特点",
            ))
        
        return results
    
    def _check_code(
        self,
        code_bundle: Dict[str, Any],
    ) -> List[ComplianceResult]:
        """检查代码材料."""
        results = []
        
        total_lines = int(code_bundle.get("total_lines") or 0)
        total_files = int(code_bundle.get("total_files") or 0)
        pages = code_bundle.get("pages_data") or []
        has_enough = code_bundle.get("has_enough_code", False)
        
        # 检查代码行数
        if total_lines >= 3000:
            results.append(ComplianceResult(
                rule_id="CODE_001",
                rule_name="代码总行数",
                category=CheckCategory.CODE,
                status=CheckStatus.PASSED,
                message=f"代码共 {total_lines} 行",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="CODE_001",
                rule_name="代码总行数",
                category=CheckCategory.CODE,
                status=CheckStatus.FAILED,
                message=f"代码仅 {total_lines} 行，不足3000行",
                suggestion="请补充更多代码",
            ))
        
        # 检查代码文件数
        if total_files >= 5:
            results.append(ComplianceResult(
                rule_id="CODE_002",
                rule_name="代码文件数",
                category=CheckCategory.CODE,
                status=CheckStatus.PASSED,
                message=f"共 {total_files} 个代码文件",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="CODE_002",
                rule_name="代码文件数",
                category=CheckCategory.CODE,
                status=CheckStatus.WARNING,
                message=f"仅 {total_files} 个代码文件，建议不少于5个",
            ))
        
        # 检查页数
        if len(pages) >= 60:
            results.append(ComplianceResult(
                rule_id="CODE_003",
                rule_name="代码页数",
                category=CheckCategory.CODE,
                status=CheckStatus.PASSED,
                message=f"共 {len(pages)} 页",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="CODE_003",
                rule_name="代码页数",
                category=CheckCategory.CODE,
                status=CheckStatus.WARNING,
                message=f"仅 {len(pages)} 页",
                suggestion="代码页数应为60页（前30页+后30页）",
            ))
        
        return results
    
    def _check_manual(
        self,
        manual: Dict[str, Any],
    ) -> List[ComplianceResult]:
        """检查说明书."""
        results = []
        
        title = manual.get("title", "")
        # None 安全：DB 中 page_count/word_count 可显式为 None（如新生成草稿未统计），
        # dict.get(key, default) 仅在 key 缺失时用默认值，值为 None 时仍返回 None，
        # 直接参与 >= 比较会抛 TypeError。统一强制转 int。
        page_count = int(manual.get("page_count") or 0)
        word_count = int(manual.get("word_count") or 0)
        has_toc = manual.get("has_toc", False)
        has_chapters = manual.get("has_chapters", False)
        
        # 检查标题
        if title:
            results.append(ComplianceResult(
                rule_id="MANUAL_001",
                rule_name="说明书标题",
                category=CheckCategory.MANUAL,
                status=CheckStatus.PASSED,
                message=f"标题: {title}",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="MANUAL_001",
                rule_name="说明书标题",
                category=CheckCategory.MANUAL,
                status=CheckStatus.FAILED,
                message="说明书标题不能为空",
            ))
        
        # 检查页数
        if page_count >= 15:
            results.append(ComplianceResult(
                rule_id="MANUAL_002",
                rule_name="说明书页数",
                category=CheckCategory.MANUAL,
                status=CheckStatus.PASSED,
                message=f"共 {page_count} 页",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="MANUAL_002",
                rule_name="说明书页数",
                category=CheckCategory.MANUAL,
                status=CheckStatus.FAILED,
                message=f"仅 {page_count} 页，不足15页",
                suggestion="请补充说明书内容",
            ))
        
        # 检查字数
        if word_count >= 3000:
            results.append(ComplianceResult(
                rule_id="MANUAL_003",
                rule_name="说明书字数",
                category=CheckCategory.MANUAL,
                status=CheckStatus.PASSED,
                message=f"共 {word_count} 字",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="MANUAL_003",
                rule_name="说明书字数",
                category=CheckCategory.MANUAL,
                status=CheckStatus.WARNING,
                message=f"仅 {word_count} 字，建议不少于3000字",
            ))
        
        # 检查目录
        if has_toc:
            results.append(ComplianceResult(
                rule_id="MANUAL_004",
                rule_name="目录",
                category=CheckCategory.MANUAL,
                status=CheckStatus.PASSED,
                message="已添加目录",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="MANUAL_004",
                rule_name="目录",
                category=CheckCategory.MANUAL,
                status=CheckStatus.WARNING,
                message="未添加目录",
                suggestion="建议添加目录以便查阅",
            ))
        
        # 检查章节结构
        if has_chapters:
            results.append(ComplianceResult(
                rule_id="MANUAL_005",
                rule_name="章节结构",
                category=CheckCategory.MANUAL,
                status=CheckStatus.PASSED,
                message="已添加规范章节结构",
            ))
        else:
            results.append(ComplianceResult(
                rule_id="MANUAL_005",
                rule_name="章节结构",
                category=CheckCategory.MANUAL,
                status=CheckStatus.WARNING,
                message="未添加规范章节结构",
                suggestion="建议添加：软件概述、功能介绍、操作说明等章节",
            ))
        
        return results
