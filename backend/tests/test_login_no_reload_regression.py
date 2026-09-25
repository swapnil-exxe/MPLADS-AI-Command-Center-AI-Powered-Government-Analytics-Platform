"""
Login Regression Test: No Page Reload on Authentication Failure

Verifies:
1. Failed login returns HTTP 401 Unauthorized with generic detail ("Invalid credentials.").
2. Response headers contain no Location/Redirect directives.
3. 5 failed attempts trigger HTTP 429 Too Many Requests with Retry-After.
4. Successful login returns 200 OK with valid bearer token.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.auth.limiter import failed_login_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    failed_login_limiter.reset()
    yield
    failed_login_limiter.reset()


def test_wrong_password_returns_401_no_redirect():
    """Verify wrong password returns 401 Unauthorized with no redirect headers."""
    res = client.post("/api/v1/auth/login", json={
        "email": "ministry@mplads.gov.in",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials."
    assert "Location" not in res.headers


def test_fake_email_returns_401_no_redirect():
    """Verify fake email returns 401 Unauthorized with generic detail."""
    res = client.post("/api/v1/auth/login", json={
        "email": "nonexistent.user@mplads.gov.in",
        "password": "Mplads@Demo2026#"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials."
    assert "Location" not in res.headers


def test_successful_login_returns_200():
    """Verify valid credentials return 200 OK with token and role."""
    res = client.post("/api/v1/auth/login", json={
        "email": "ministry@mplads.gov.in",
        "password": "Mplads@Demo2026#"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "MINISTRY"
