from typing import Annotated, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.config import settings
from api.dependencies import get_db
from database.models import User
from api.auth.security import decode_access_token

# OAuth2 password bearer pointing to the login route
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT access token cryptographically, then fetches user from database
    via primary key to guarantee real-time validation of active status and jurisdiction.
    """
    payload = decode_access_token(token)
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject claim (sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: subject claim must be integer user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensures the authenticated user is currently active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated. Access revoked.",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_active_user)]

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def get_optional_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme_optional)] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns authenticated User if valid token is provided, or None if unauthenticated.
    Prevents 401 error on public analytics endpoints while supporting RBAC scoping when logged in.
    """
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = int(user_id_str)
        user = db.query(User).filter(User.id == user_id).first()
        return user if (user and user.is_active) else None
    except Exception:
        return None

OptionalUser = Annotated[Optional[User], Depends(get_optional_current_user)]


def require_roles(allowed_roles: List[str]):
    """FastAPI dependency factory to enforce role-based access control."""
    def role_verifier(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: Role '{current_user.role}' is not authorized for this resource. "
                    f"Required roles: {allowed_roles}"
                )
            )
        return current_user
    return role_verifier
