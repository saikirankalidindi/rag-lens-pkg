"""
Auth security utilities.

Provides:
  - Password hashing / verification  (bcrypt via passlib)
  - JWT creation / decoding           (python-jose)

Never call these from outside app/auth — always go through the service layer.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# bcrypt context — auto-selects the strongest available rounds
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT algorithm
_ALGORITHM = "HS256"


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    *,
    expires_delta: Optional[timedelta] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT.

    Args:
        subject: The ``sub`` claim — typically the user's ID.
        expires_delta: Override the default expiry.
        extra: Additional claims merged into the payload.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT.

    Raises:
        JWTError: If the token is invalid, expired, or tampered with.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
