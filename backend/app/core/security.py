"""安全相关：密码哈希、JWT 生成与解析。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def get_password_hash(password: str) -> str:
    """生成密码哈希（bcrypt）。"""

    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("密码过长：bcrypt 最多支持 72 字节，请缩短密码或改用其他算法。")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验密码。"""

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    subject: str,
    roles: list[str] | None = None,
    expires_minutes: int | None = None,
    jti: str | None = None,
) -> str:
    """创建 AccessToken（JWT）。"""

    expire_minutes = (
        expires_minutes if expires_minutes is not None else settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire_at = datetime.now(UTC) + timedelta(minutes=expire_minutes)
    token_id = jti or uuid4().hex

    payload = {
        "sub": subject,
        "roles": roles or [],
        "exp": expire_at,
        "iat": datetime.now(UTC),
        "jti": token_id,
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """解析 AccessToken（失败返回 None）。"""

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None
