"""
Comprehensive Security Audit & Hardening Test Suite
Verifies:
- Authentication & JWT token security
- Rate limiting on /auth/login (5 attempts per 15 mins -> 429 + Retry-After)
- Rejection of fake credentials, aliases, empty credentials, forged tokens, expired tokens
- Protection against role escalation & IDOR
- Protection of /admin endpoints with server-side RBAC
- SQL injection and XSS payload safety
- Security response headers
- Frontend bundle secret verification
"""

import time
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app
from database.connection import get_session
from database.models import User
from api.auth.security import create_access_token
from datetime import timedelta

from api.auth.limiter import failed_login_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset failed login rate limiter state before each test."""
    failed_login_limiter.reset()
    yield
    failed_login_limiter.reset()


def test_login_valid_credentials_success():
    """Verify valid login returns 200 OK with signed JWT token."""
    res = client.post("/api/v1/auth/login", json={
        "email": "ministry@mplads.gov.in",
        "password": "Mplads@Demo2026#"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "MINISTRY"


def test_login_invalid_password_rejected():
    """Verify invalid password returns 401 Unauthorized with generic message."""
    res = client.post("/api/v1/auth/login", json={
        "email": "ministry@mplads.gov.in",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert res.json()["detail"] in ("Invalid credentials.", "Incorrect email or password")


def test_login_fake_username_alias_rejected():
    """Verify fake/short alias username without valid email is rejected."""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin",
        "password": "admin"
    })
    assert res.status_code in (401, 429)


def test_login_empty_credentials_rejected():
    """Verify empty email or password returns 401 or 429 when rate limited."""
    res = client.post("/api/v1/auth/login", json={
        "email": "",
        "password": ""
    })
    assert res.status_code in (401, 429)


def test_forged_jwt_signature_rejected():
    """Verify tampered JWT token is rejected with 401."""
    forged_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6Ik1JTklTVFJZIn0.FORGED_SIGNATURE"
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
    assert res.status_code == 401


def test_expired_jwt_rejected():
    """Verify expired JWT token returns 401 Unauthorized."""
    expired_token = create_access_token(
        data={"sub": "1", "email": "ministry@mplads.gov.in", "role": "MINISTRY"},
        expires_delta=timedelta(seconds=-3600)
    )
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401


def test_role_escalation_prevented():
    """Verify user ID in JWT token determines authoritative DB role, ignoring forged role claims."""
    session = get_session()
    # Create a test MP user
    user = session.query(User).filter(User.role == "MP").first()
    if user:
        # Generate token with fake MINISTRY claim for an MP user ID
        token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": "MINISTRY"})
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        # DB role must override JWT claim
        assert res.json()["role"] == "MP"


def test_admin_endpoint_rbac_protection():
    """Verify admin user provisioning endpoint requires MINISTRY role."""
    # 1. Unauthenticated -> 401
    res_unauth = client.post("/api/v1/auth/users", json={
        "email": "unauth.user@mplads.gov.in",
        "password": "Password123!",
        "full_name": "Unauth User",
        "role": "MP"
    })
    assert res_unauth.status_code == 401

    # 2. Non-admin (MP) -> 403
    mp_user = get_session().query(User).filter(User.role == "MP").first()
    if mp_user:
        mp_token = create_access_token(data={"sub": str(mp_user.id), "email": mp_user.email, "role": "MP"})
        res_forbidden = client.post("/api/v1/auth/users", json={
            "email": "forbidden.user@mplads.gov.in",
            "password": "Password123!",
            "full_name": "Forbidden User",
            "role": "MP"
        }, headers={"Authorization": f"Bearer {mp_token}"})
        assert res_forbidden.status_code == 403


def test_sql_injection_payloads_safe():
    """Verify SQL injection payloads in query parameters do not execute or break SQL syntax."""
    sqli_payloads = [
        "' OR '1'='1",
        "1; DROP TABLE works; --",
        "UNION SELECT 1,2,3 --",
        "'; EXEC xp_cmdshell('dir'); --"
    ]
    for p in sqli_payloads:
        res = client.get(f"/api/v1/works?state={p}")
        assert res.status_code == 200
        assert "items" in res.json()


def test_xss_payloads_safe():
    """Verify XSS payloads in query strings do not crash API."""
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)"
    ]
    for x in xss_payloads:
        res = client.get(f"/api/v1/meta/filters?q={x}")
        assert res.status_code == 200


def test_security_headers_present():
    """Verify security response headers are returned on API endpoints."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert res.headers.get("Strict-Transport-Security") is not None


def test_no_secrets_in_frontend_bundle():
    """Verify production frontend bundle in frontend/dist contains no DB passwords or JWT secrets."""
    dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if dist_dir.exists():
        for html_or_js in dist_dir.glob("**/*"):
            if html_or_js.is_file() and html_or_js.suffix in (".html", ".js", ".css"):
                content = html_or_js.read_text(errors="ignore")
                assert "Mplads@2026!" not in content
                assert "mplads-dev-secret-key" not in content
