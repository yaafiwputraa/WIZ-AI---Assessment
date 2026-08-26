import base64
import hashlib
import hmac
import secrets
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .errors import APIError
from .models import StaffRole, StaffUser

PASSWORD_ITERATIONS = 600_000
JWT_ALGORITHM = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode()}$"
        f"{base64.urlsafe_b64encode(digest).decode()}"
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def authenticate_staff(db: Session, email: str, password: str) -> StaffUser | None:
    user = db.scalar(
        select(StaffUser).where(func.lower(StaffUser.email) == email.strip().lower())
    )
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(user: StaffUser) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.jwt_access_token_minutes)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "iat": now,
            "exp": expires,
        },
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    return token, settings.jwt_access_token_minutes * 60


def get_current_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> StaffUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise APIError(401, "authentication_required", "Staff authentication is required.")
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_settings().jwt_secret,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = uuid.UUID(str(payload.get("sub", "")))
    except (InvalidTokenError, ValueError) as exc:
        raise APIError(401, "invalid_token", "The access token is invalid or expired.") from exc
    user = db.get(StaffUser, user_id)
    if user is None or not user.is_active:
        raise APIError(401, "invalid_token", "The staff account is unavailable.")
    if payload.get("role") != user.role.value:
        raise APIError(401, "invalid_token", "The access token is no longer valid.")
    return user


def require_roles(*allowed_roles: StaffRole) -> Callable[..., StaffUser]:
    def role_dependency(user: StaffUser = Depends(get_current_staff)) -> StaffUser:
        if user.role not in allowed_roles:
            raise APIError(
                403,
                "insufficient_role",
                "Your role is not allowed to perform this action.",
            )
        return user

    return role_dependency
