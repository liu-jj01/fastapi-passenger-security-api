from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session
from app.models import User


password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    auto_error=False,
)


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


def decode_access_token(token: str) -> dict[str, Any]:
    """验证并解析 JWT。"""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def build_credentials_exception(
    message: str = "无效或已过期的访问令牌",
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
    token: Annotated[
        str | None,
        Depends(oauth2_scheme),
    ],
    session: Session = Depends(get_session),
) -> User:
    """根据 Bearer Token 获取当前用户。"""
    if token is None:
        raise build_credentials_exception(
            "缺少 Bearer Token"
        )

    try:
        payload = decode_access_token(token)
    except InvalidTokenError as error:
        raise build_credentials_exception() from error

    username = payload.get("sub")

    if not isinstance(username, str) or not username:
        raise build_credentials_exception()

    user = session.scalar(
        select(User).where(User.username == username)
    )

    if user is None:
        raise build_credentials_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user