"""安全模块 - JWT 认证和密码哈希."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from ipflow.config import get_settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码.
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        密码是否匹配
    """
    plain_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """获取密码哈希.
    
    Args:
        password: 明文密码
        
    Returns:
        哈希后的密码
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """创建访问令牌.
    
    Args:
        user_id: 用户 ID
        expires_delta: 过期时间增量，默认使用配置值
        
    Returns:
        JWT 访问令牌
    """
    settings = get_settings()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """创建刷新令牌.
    
    Args:
        user_id: 用户 ID
        
    Returns:
        JWT 刷新令牌
    """
    settings = get_settings()
    
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_urlsafe(32)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": jti,
        "iat": datetime.utcnow(),
    }
    
    # TODO: 存储到 Redis 用于失效管理
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_access_token(token: str) -> str:
    """验证访问令牌.
    
    Args:
        token: JWT 令牌
        
    Returns:
        用户 ID
        
    Raises:
        ValueError: 令牌无效或过期
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 验证类型
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token: missing subject")
        
        return user_id
        
    except JWTError:
        raise ValueError("Invalid token")


def verify_refresh_token(token: str) -> str:
    """验证刷新令牌.
    
    Args:
        token: JWT 刷新令牌
        
    Returns:
        用户 ID
        
    Raises:
        ValueError: 令牌无效或过期
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 验证类型
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token: missing subject")
        
        # TODO: 检查 Redis 黑名单
        
        return user_id
        
    except JWTError:
        raise ValueError("Invalid token")
