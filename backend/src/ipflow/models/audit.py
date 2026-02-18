"""审计日志模型.

记录系统中的关键操作。
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    """审计日志模型.
    
    Attributes:
        id: 日志唯一标识
        user_id: 操作用户ID
        organization_id: 组织ID
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        old_values: 旧值
        new_values: 新值
        ip_address: IP地址
        user_agent: 用户代理
        request_id: 请求ID
        created_at: 创建时间
    """
    
    __tablename__ = "audit_log"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 用户信息
    user_id: Optional[UUID] = Field(default=None, sa_column=Column(ForeignKey("user.id"), nullable=True, index=True))
    organization_id: Optional[UUID] = Field(default=None, sa_column=Column(ForeignKey("organization.id"), nullable=True, index=True))
    
    # 操作信息
    action: str = Field(sa_column=Column(String(50), nullable=False, index=True))
    # action 示例: create, update, delete, login, logout, export, invite
    
    resource_type: str = Field(sa_column=Column(String(50), nullable=False))
    # resource_type 示例: project, user, organization, code_bundle, manual
    
    resource_id: Optional[UUID] = Field(default=None, sa_column=Column(ForeignKey("project.id"), nullable=True))
    
    # 变更详情
    old_values: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    new_values: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    # 请求信息
    ip_address: Optional[str] = Field(default=None, sa_column=Column(String(45), nullable=True))
    user_agent: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    request_id: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True, index=True))
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False, index=True))


class AuditLogService:
    """审计日志服务.
    
    提供审计日志记录和查询功能。
    """
    
    def __init__(self, db):
        self.db = db
    
    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """记录审计日志.
        
        Args:
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            user_id: 用户ID
            organization_id: 组织ID
            old_values: 旧值
            new_values: 新值
            description: 描述
            ip_address: IP地址
            user_agent: 用户代理
            request_id: 请求ID
            
        Returns:
            创建的审计日志
        """
        log = AuditLog(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        self.db.add(log)
        await self.db.commit()
        return log
    
    async def get_logs(
        self,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        """查询审计日志.
        
        Args:
            organization_id: 组织ID筛选
            user_id: 用户ID筛选
            action: 操作类型筛选
            resource_type: 资源类型筛选
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            日志列表
        """
        from sqlalchemy import select, desc
        
        query = select(AuditLog).order_by(desc(AuditLog.created_at))
        
        if organization_id:
            query = query.where(AuditLog.organization_id == organization_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
