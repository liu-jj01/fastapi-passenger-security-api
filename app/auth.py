from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """将明文密码转换为安全的密码哈希。"""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """验证明文密码是否与数据库中的哈希值匹配。"""
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """为指定用户生成 JWT 访问令牌。"""
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )

    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )