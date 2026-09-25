from api.auth.security import (
    hash_password,
    verify_password,
    verify_dummy_password,
    create_access_token,
    decode_access_token,
)
from api.auth.limiter import limiter
from api.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_optional_current_user,
    require_roles,
    CurrentUser,
    OptionalUser,
)
from api.auth.scoping import (
    apply_jurisdiction_scope,
    apply_work_joined_scope,
    apply_duplicate_works_scope,
    verify_work_jurisdiction,
)

__all__ = [
    "hash_password",
    "verify_password",
    "verify_dummy_password",
    "create_access_token",
    "decode_access_token",
    "limiter",
    "get_current_user",
    "get_current_active_user",
    "get_optional_current_user",
    "require_roles",
    "CurrentUser",
    "OptionalUser",
    "apply_jurisdiction_scope",
    "apply_work_joined_scope",
    "apply_duplicate_works_scope",
    "verify_work_jurisdiction",
]

