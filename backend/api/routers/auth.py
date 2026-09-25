from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.config import settings
from api.dependencies import get_db
from database.models import User
from api.schemas.auth import LoginRequest, TokenResponse, UserRead, UserCreate
from api.auth.security import (
    hash_password,
    verify_password,
    verify_dummy_password,
    create_access_token,
)
from api.auth.dependencies import CurrentUser, require_roles
from api.auth.limiter import limiter, failed_login_limiter

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post("/login", response_model=TokenResponse)
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user with email and password.
    Returns an RFC 7519 compliant signed JWT access token.
    Rate limited to 5 failed attempts per 15 minutes per IP address.
    Successful logins do not count as failures.
    Includes constant-time dummy verification to mitigate timing-based user enumeration.
    """
    # 1. Enforce failed login rate limiting
    failed_login_limiter.check(request)

    clean_email = credentials.email.lower().strip()
    if not clean_email or not credentials.password:
        failed_login_limiter.record_failure(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == clean_email).first()

    if not user:
        # Mitigate timing attacks by running equalizing dummy bcrypt computation
        verify_dummy_password()
        failed_login_limiter.record_failure(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    valid_pass = verify_password(credentials.password, user.hashed_password)

    if not valid_pass:
        failed_login_limiter.record_failure(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        failed_login_limiter.record_failure(request)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated. Contact system administrator.",
        )

    # Clear failure counter on valid authentication
    failed_login_limiter.record_success(request)

    # Construct claims payload
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "state": user.assigned_state,
        "district": user.assigned_district,
        "mp_name": user.assigned_mp_name,
    }

    access_token = create_access_token(data=token_claims)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        email=user.email,
        full_name=user.full_name,
        assigned_state=user.assigned_state,
        assigned_district=user.assigned_district,
        assigned_mp_name=user.assigned_mp_name,
    )


@router.get("/me", response_model=UserRead)
def get_current_user_profile(current_user: CurrentUser):
    """
    Returns the authenticated user's profile and active jurisdictional boundaries.
    """
    return UserRead.model_validate(current_user)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_admin: User = Depends(require_roles(["MINISTRY"])),
    db: Session = Depends(get_db)
):
    """
    Administrative endpoint for provisioning new stakeholder accounts.
    Restricted exclusively to Central Ministry (MINISTRY) administrators.
    """
    clean_email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{clean_email}' already exists.",
        )

    # Validate role-specific jurisdictional assignments
    if payload.role in ("STATE_OFFICER", "DISTRICT_OFFICER") and not payload.assigned_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.role}' requires an 'assigned_state'.",
        )
    if payload.role == "DISTRICT_OFFICER" and not payload.assigned_district:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role 'DISTRICT_OFFICER' requires an 'assigned_district'.",
        )
    if payload.role == "MP" and not payload.assigned_mp_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role 'MP' requires an 'assigned_mp_name'.",
        )

    new_user = User(
        email=clean_email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role,
        assigned_state=payload.assigned_state,
        assigned_district=payload.assigned_district,
        assigned_mp_name=payload.assigned_mp_name,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserRead.model_validate(new_user)
