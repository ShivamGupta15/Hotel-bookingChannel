import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


ACCESS_TOKEN_EXPIRE_MINUTES = 60
bearer_scheme = HTTPBearer()


def _required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be configured")
    return value


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    password_hash = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
    )
    encode = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"scrypt${encode(salt)}${encode(password_hash)}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, encoded_salt, encoded_password_hash = encoded_hash.split("$", 2)
        if algorithm != "scrypt":
            return False

        decode = lambda value: base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        salt = decode(encoded_salt)
        expected_hash = decode(encoded_password_hash)
        actual_hash = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=len(expected_hash),
        )
        return hmac.compare_digest(actual_hash, expected_hash)
    except (ValueError, TypeError):
        return False


def authenticate_admin(username: str, password: str) -> bool:
    configured_username = _required_setting("ADMIN_USERNAME")
    configured_password_hash = _required_setting("ADMIN_PASSWORD_HASH")
    return hmac.compare_digest(username, configured_username) and verify_password(
        password,
        configured_password_hash,
    )


def create_access_token() -> tuple[str, int]:
    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload = {
        "sub": _required_setting("ADMIN_USERNAME"),
        "role": "admin",
        "exp": expires_at,
    }
    token = jwt.encode(
        payload,
        _required_setting("JWT_SECRET_KEY"),
        algorithm="HS256",
    )
    return token, expires_in


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired admin session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            _required_setting("JWT_SECRET_KEY"),
            algorithms=["HS256"],
        )
        if payload.get("role") != "admin" or not payload.get("sub"):
            raise credentials_error
        return payload
    except (jwt.InvalidTokenError, RuntimeError):
        raise credentials_error