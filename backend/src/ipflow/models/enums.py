"""枚举定义模块.

定义项目中使用的所有枚举类型。
"""

from enum import Enum


class ProjectType(str, Enum):
    """项目类型枚举."""
    
    COPYRIGHT = "copyright"      # 软件著作权
    PATENT = "patent"            # 专利
    TRADEMARK = "trademark"      # 商标


class ProjectStatus(str, Enum):
    """项目状态枚举."""
    
    DRAFT = "draft"                          # 草稿
    IN_PROGRESS = "in_progress"              # 进行中
    REVIEWING = "reviewing"                  # 审核中
    PENDING_SUBMIT = "pending_submit"        # 待提交
    SUBMITTED = "submitted"                  # 已提交
    ACCEPTED = "accepted"                    # 已受理
    APPROVED = "approved"                    # 已通过
    REJECTED = "rejected"                    # 被驳回
    WITHDRAWN = "withdrawn"                  # 已撤回


class SubjectType(str, Enum):
    """主体类型枚举."""
    
    INDIVIDUAL = "individual"        # 个人
    ENTERPRISE = "enterprise"        # 企业
    INSTITUTION = "institution"      # 高校/研究机构
    AGENCY = "agency"                # 代理机构


class ManualTemplateType(str, Enum):
    """说明书模板类型枚举."""
    
    WEB = "web"              # Web应用
    MOBILE = "mobile"        # 移动应用
    ALGORITHM = "algorithm"  # 算法/工具类
    SCRIPT = "script"        # 脚本/插件
    DESKTOP = "desktop"      # 桌面应用


class DevelopmentMethod(str, Enum):
    """开发方式枚举."""
    
    INDEPENDENT = "independent"      # 独立开发
    COOPERATIVE = "cooperative"      # 合作开发
    COMMISSION = "commission"        # 委托开发
    ASSIGNMENT = "assignment"        # 任务下达


class PublicationStatus(str, Enum):
    """发表状态枚举."""
    
    PUBLISHED = "published"          # 已发表
    UNPUBLISHED = "unpublished"      # 未发表
