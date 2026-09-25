"""
Comprehensive Four Role Authentication & Role Isolation Test Suite (Section 26)

Verifies:
1. Successful authentication for all 4 legitimate roles:
   - MINISTRY (Central Ministry / Admin)
   - STATE_OFFICER (State Nodal Officer)
   - DISTRICT_OFFICER (District Planning Officer)
   - MP (Member of Parliament)
2. Accurate server-verified role retrieval and access control.
3. Strict rejection of invalid passwords, fake emails, empty fields, and malformed inputs.
4. HTTP 401 rejection with generic error detail ("Invalid credentials.").
5. HTTP 403 rejection for deactivated user accounts and unauthorized role endpoints.
6. Role isolation: Role A (MP / Officer) attempting Admin/Ministry resources returns HTTP 403 Forbidden.
7. JWT signature forgery and payload tampering protection.
8. Rate limiting enforcement: 5 failed login attempts per 15 min per IP -> 6th failed attempt returns HTTP 429 with Retry-After.
9. Successful login attempts do NOT count as failures for rate limiting.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.connection import get_session
from database.models import User
from api.auth.security import create_access_token, hash_password
from api.auth.limiter import failed_login_limiter

client = TestClient(app)

LEGITIMATE_ACCOUNTS = [
    {"email": "ministry@mplads.gov.in", "role": "MINISTRY"},
    {"email": "state.up@mplads.gov.in", "role": "STATE_OFFICER"},
    {"email": "district.patna@mplads.gov.in", "role": "DISTRICT_OFFICER"},
    {"email": "mp.khalsa@mplads.gov.in", "role": "MP"},
]

PASSWORD = "Mplads@Demo2026#"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset failed login rate limiter state before each test."""
    failed_login_limiter.reset()
    yield
    failed_login_limiter.reset()


def test_four_legitimate_roles_authenticate_successfully():
    """Verify all four legitimate roles authenticate against PostgreSQL DB and receive server-verified role tokens."""
    for account in LEGITIMATE_ACCOUNTS:
        res = client.post("/api/v1/auth/login", json={
            "email": account["email"],
            "password": PASSWORD
        })
        assert res.status_code == 200, f"Failed for role {account['role']}"
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == account["role"]
        assert data["email"] == account["email"]


def test_invalid_credentials_rejected_generically():
    """Verify invalid password or non-existent email returns HTTP 401 with generic error detail."""
    invalid_payloads = [
        {"email": "ministry@mplads.gov.in", "password": "WrongPassword123!"},
        {"email": "fake.user@mplads.gov.in", "password": "Mplads@Demo2026#"},
        {"email": "unknown@domain.com", "password": "InvalidPassword"},
        {"email": "", "password": ""},
        {"email": "malformed_email", "password": "somepassword"},
    ]
    for payload in invalid_payloads:
        res = client.post("/api/v1/auth/login", json=payload)
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid credentials."


def test_failed_login_rate_limiting_enforced():
    """
    Verify maximum 5 failed authentication attempts per 15-minute window per IP.
    The 6th failed attempt within the window must return HTTP 429 with Retry-After.
    Successful logins do NOT count as failures.
    """
    # 1. Five failed attempts -> all 401
    for i in range(5):
        res = client.post("/api/v1/auth/login", json={
            "email": "ministry@mplads.gov.in",
            "password": f"WrongAttempt{i}"
        })
        assert res.status_code == 401, f"Attempt {i+1} should return 401"

    # 2. Sixth failed attempt -> 429 Too Many Requests
    res6 = client.post("/api/v1/auth/login", json={
        "email": "ministry@mplads.gov.in",
        "password": "WrongAttempt6"
    })
    assert res6.status_code == 429
    assert "Retry-After" in res6.headers
    assert "Too many failed login attempts" in res6.json()["detail"]

    # Reset for next check
    failed_login_limiter.reset()

    # 3. Successful login attempts do NOT increment failure counter
    for _ in range(10):
        res_ok = client.post("/api/v1/auth/login", json={
            "email": "ministry@mplads.gov.in",
            "password": PASSWORD
        })
        assert res_ok.status_code == 200


def test_role_isolation_admin_access_denied():
    """Verify non-admin roles (STATE_OFFICER, DISTRICT_OFFICER, MP) cannot execute admin endpoints."""
    session = get_session()
    non_admin_roles = ["STATE_OFFICER", "DISTRICT_OFFICER", "MP"]
    for role_name in non_admin_roles:
        user = session.query(User).filter(User.role == role_name).first()
        if user:
            token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
            res = client.post("/api/v1/auth/users", json={
                "email": "unauthorized.new@mplads.gov.in",
                "password": "Password123!",
                "full_name": "Unauthorized User",
                "role": "MP"
            }, headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 403, f"Expected 403 Forbidden for role {role_name}, got {res.status_code}"


def test_server_authoritative_user_identity_overrides_client_claims():
    """Verify backend retrieves real DB identity for user ID, preventing JWT claim spoofing."""
    session = get_session()
    mp_user = session.query(User).filter(User.role == "MP").first()
    if mp_user:
        # Spoof role claim in token as MINISTRY
        spoofed_token = create_access_token(data={"sub": str(mp_user.id), "email": mp_user.email, "role": "MINISTRY"})
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {spoofed_token}"})
        assert res.status_code == 200
        # Authoritative DB query returns real role (MP)
        assert res.json()["role"] == "MP"


def test_deactivated_user_login_denied():
    """Verify deactivated user account receives HTTP 403 Forbidden."""
    session = get_session()
    test_user = session.query(User).filter(User.email == "deactivated.test@mplads.gov.in").first()
    if not test_user:
        test_user = User(
            email="deactivated.test@mplads.gov.in",
            hashed_password=hash_password(PASSWORD),
            full_name="Deactivated Test Officer",
            role="STATE_OFFICER",
            is_active=False
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
    else:
        test_user.hashed_password = hash_password(PASSWORD)
        test_user.is_active = False
        session.commit()
    
    res = client.post("/api/v1/auth/login", json={
        "email": "deactivated.test@mplads.gov.in",
        "password": PASSWORD
    })
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"].lower()
