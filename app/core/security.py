# app/core/security.py
# 密码和token处理文件
from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# 使用现代且安全的 CryptContext 配置
# deprecated="auto" 会自动处理未来算法的迁移
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
        subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    创建 JWT 访问令牌。
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配。

    注意：bcrypt 有 72 字节的硬性限制。此函数在验证前会自动截断过长的密码，
    以防止 ValueError 异常，同时保持向后兼容性。
    """
    # 将密码编码为字节，以准确计算其长度
    password_bytes = plain_password.encode('utf-8')

    # 如果密码超过 72 字节，则截断它
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        # 可选：记录一个警告，告知用户密码被截断
        # import logging
        # logging.warning(f"Password was truncated to 72 bytes for verification.")

    # 将（可能被截断的）字节解码回字符串以进行验证
    # errors='ignore' 会安全地丢弃任何因截断而产生的不完整的多字节字符
    truncated_password = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.verify(truncated_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    为明文密码生成哈希值。
    """
    # 在哈希之前也进行截断，以确保数据库中的哈希值始终来自 <= 72 字节的密码
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    password_to_hash = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.hash(password_to_hash)

