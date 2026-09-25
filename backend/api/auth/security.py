from typing import Optional
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import HTTPException, status
from api.config import settings

# Pre-computed 12-round dummy bcrypt hash used to equalize execution time on non-existent users
DUMMY_BCRYPT_HASH = b"$2b$12$FbacKDkjRSFsxlU8NJ3jWuvYaIXmR69W1qMkD8D81B6zqcQkWwT8m"


def hash_password(password: str) -> str:
    """Hash password using bcrypt with standard cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def verify_dummy_password() -> None:
    """Execute a dummy 12-round bcrypt comparison to mitigate timing attacks on invalid emails."""
    try:
        bcrypt.checkpw(b"dummy_timing_mitigation_password", DUMMY_BCRYPT_HASH)
    except Exception:
        pass


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed RFC 7519 JWT access token with subject, identity, and jurisdiction claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Cryptographically verify and decode a JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception
