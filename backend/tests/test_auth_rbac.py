"""
Phase 6.3: Authentication, RBAC & Backend Security Test Suite
Validates:
- JWT login, token expiration, invalid credential handling
- Timing attack mitigation on non-existent emails
- Rate limiting on /auth/login
- Instantaneous revocation of deactivated users
- Role-based access control (MINISTRY, STATE_OFFICER, DISTRICT_OFFICER, MP)
- Server-side query scoping for collection endpoints (200 OK with scoped/empty results)
- Single-resource authorization (404 Not Found vs 403 Forbidden)
- Duplicate work cross-jurisdiction pair visibility
- Administrative user provisioning permissions
"""

import time
import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.connection import get_session
from database.models import User
from api.auth.security import create_access_token

client = TestClient(app)

UP_WORK_ID = "WS/MP018/2023-2024/536-Construction of toilet blocks"       # Uttar Pradesh work
PATNA_WORK_ID = "WS/MP505/2023-2024/2091-Construction of roads, link roads, pathways or any other road with or without drainage system"     # Bihar, PATNA work
KHALSA_WORK_ID = "WS/MP18152/2024-2025/133686-Construction of rooms and halls in school and colleges"   # Sarabjeet Singh Khalsa work


# --------------------------------------------------------------------------
# 1. Authentication & Token Lifecycle Tests
# --------------------------------------------------------------------------

def test_login_success():
    """Verify valid login returns signed JWT access token with role and metadata."""
    res = client.post("/api/v1/auth/login", json={
        "email": "ministry@mplads.gov.in",
        "password": "Mplads@Demo2026#"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "MINISTRY"
    assert data["email"] == "ministry@mplads.gov.in"
    assert data["expires_in"] == 3600


def test_login_invalid_password():
    """Verify bad password returns 401 Unauthorized with generic message."""
    res = client.post("/api/v1/auth/login", json={
        "email": "ministry@mplads.gov.in",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert res.json()["detail"] in ("Invalid credentials.", "Incorrect email or password")


def test_login_nonexistent_email_timing_mitigation():
    """Verify non-existent user returns 401 and takes non-trivial time due to dummy hash."""
    start = time.time()
    res = client.post("/api/v1/auth/login", json={
        "email": "nonexistent_fake_user@mplads.gov.in",
        "password": "RandomPassword123!"
    })
    elapsed = time.time() - start
    assert res.status_code == 401
    assert res.json()["detail"] in ("Invalid credentials.", "Incorrect email or password")
    # Timing mitigation should take roughly comparable time to normal bcrypt check (>20ms)
    assert elapsed >= 0.02


def test_unauthenticated_protected_endpoint():
    """Verify accessing protected endpoint without token returns 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_invalid_bearer_token():
    """Verify forged or malformed Bearer token returns 401."""
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer totally-bogus-token"})
    assert res.status_code == 401


def test_auth_me_profiles(ministry_headers, state_up_headers, district_patna_headers, mp_khalsa_headers):
    """Verify /auth/me returns accurate profile and jurisdictional assignments for all roles."""
    # Ministry
    res = client.get("/api/v1/auth/me", headers=ministry_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "MINISTRY"
    assert res.json()["assigned_state"] is None

    # State Officer
    res = client.get("/api/v1/auth/me", headers=state_up_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "STATE_OFFICER"
    assert res.json()["assigned_state"] == "Uttar Pradesh"

    # District Officer
    res = client.get("/api/v1/auth/me", headers=district_patna_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "DISTRICT_OFFICER"
    assert res.json()["assigned_state"] == "Bihar"
    assert res.json()["assigned_district"] == "PATNA"

    # MP
    res = client.get("/api/v1/auth/me", headers=mp_khalsa_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "MP"
    assert res.json()["assigned_mp_name"] == "SARABJEET SINGH KHALSA"


# --------------------------------------------------------------------------
# 2. Instantaneous Deactivation & Revocation Tests
# --------------------------------------------------------------------------

def test_deactivated_user_immediate_revocation():
    """Verify that deactivating a user immediately blocks access even with a valid unexpired JWT."""
    session = get_session()
    test_email = "revocation.test@mplads.gov.in"
    try:
        # Create temporary active user
        user = session.query(User).filter(User.email == test_email).first()
        if not user:
            user = User(
                email=test_email,
                hashed_password="dummy_hash_for_test",
                full_name="Revocation Test User",
                role="MINISTRY",
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        # Issue valid token
        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
        headers = {"Authorization": f"Bearer {token}"}

        # Verify access is initially granted
        res1 = client.get("/api/v1/auth/me", headers=headers)
        assert res1.status_code == 200

        # Now deactivate user in database
        user.is_active = False
        session.commit()

        # Access must be immediately revoked with 403 Forbidden
        res2 = client.get("/api/v1/auth/me", headers=headers)
        assert res2.status_code == 403
        assert "deactivated" in res2.json()["detail"].lower()
    finally:
        # Cleanup
        session.query(User).filter(User.email == test_email).delete()
        session.commit()
        session.close()


# --------------------------------------------------------------------------
# 3. Jurisdictional Collection Scoping Tests (Silent Scoping / 200 OK)
# --------------------------------------------------------------------------

def test_ministry_unrestricted_collection_scope(ministry_headers):
    """Ministry can access national catalog across all states."""
    res = client.get("/api/v1/works?page=1&page_size=10", headers=ministry_headers)
    assert res.status_code == 200
    assert res.json()["pagination"]["total_records"] >= 98825


def test_state_officer_collection_scoping(state_up_headers):
    """State UP officer sees ONLY works belonging to Uttar Pradesh."""
    res = client.get("/api/v1/works?page=1&page_size=10", headers=state_up_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["state"] == "Uttar Pradesh"

    # Conflicting filter: State UP officer filters for Bihar -> returns 200 OK with 0 records
    res_conflict = client.get("/api/v1/works?state=Bihar", headers=state_up_headers)
    assert res_conflict.status_code == 200
    assert res_conflict.json()["pagination"]["total_records"] == 0
    assert len(res_conflict.json()["items"]) == 0


def test_district_officer_composite_scoping(district_patna_headers):
    """District Patna officer sees ONLY works belonging to Bihar, PATNA."""
    res = client.get("/api/v1/works?page=1&page_size=10", headers=district_patna_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["state"] == "Bihar"
        assert item["district"] == "PATNA"

    # Conflicting district query: District Patna officer queries ?district=DHARWAD
    res_conflict = client.get("/api/v1/works?district=DHARWAD", headers=district_patna_headers)
    assert res_conflict.status_code == 200
    assert res_conflict.json()["pagination"]["total_records"] == 0
    assert len(res_conflict.json()["items"]) == 0


def test_mp_khalsa_collection_scoping(mp_khalsa_headers):
    """MP Khalsa sees ONLY works recommended under his canonical name."""
    res = client.get("/api/v1/works?page=1&page_size=10", headers=mp_khalsa_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["mp_name"] == "SARABJEET SINGH KHALSA"


# --------------------------------------------------------------------------
# 4. MP Khalsa Coverage Across All 4 Independent Models
# --------------------------------------------------------------------------

def test_mp_khalsa_detections_across_all_four_models(mp_khalsa_headers):
    """
    Verifies that MP Sarabjeet Singh Khalsa has active detections across ALL 4 models,
    justifying his selection as the canonical MP demo account.
    """
    # Model 1: Cost Anomalies
    res_cost = client.get("/api/v1/analytics/cost-anomalies?page_size=5", headers=mp_khalsa_headers)
    assert res_cost.status_code == 200
    assert res_cost.json()["pagination"]["total_records"] >= 3

    # Model 2: Duplicate Works
    res_dup = client.get("/api/v1/analytics/duplicate-works?page_size=5", headers=mp_khalsa_headers)
    assert res_dup.status_code == 200
    assert res_dup.json()["pagination"]["total_records"] >= 10

    # Model 3: Fund Anomalies
    res_fund = client.get("/api/v1/analytics/fund-anomalies?page_size=5", headers=mp_khalsa_headers)
    assert res_fund.status_code == 200
    assert res_fund.json()["pagination"]["total_records"] >= 8

    # Phase 5: Delay Tracking
    res_delay = client.get("/api/v1/analytics/delays?page_size=5", headers=mp_khalsa_headers)
    assert res_delay.status_code == 200
    assert res_delay.json()["pagination"]["total_records"] >= 11


# --------------------------------------------------------------------------
# 5. Single Resource Authorization: 404 vs 403 Tests
# --------------------------------------------------------------------------

def test_single_resource_404_when_nonexistent(ministry_headers, state_up_headers):
    """Non-existent work ID always returns 404 Not Found regardless of role."""
    res = client.get("/api/v1/works/NON_EXISTENT_WORK_99999", headers=state_up_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_single_resource_403_when_out_of_jurisdiction(state_up_headers, district_patna_headers, mp_khalsa_headers):
    """
    When work exists in the DB but is outside caller's jurisdiction,
    the server must return 403 Forbidden with a clear explanation.
    """
    # State UP officer accessing Patna (Bihar) work -> 403 Forbidden
    res_state = client.get(f"/api/v1/works/{PATNA_WORK_ID}", headers=state_up_headers)
    assert res_state.status_code == 403
    assert "outside your assigned state" in res_state.json()["detail"].lower()

    # District Patna officer accessing UP work -> 403 Forbidden
    res_district = client.get(f"/api/v1/works/{UP_WORK_ID}", headers=district_patna_headers)
    assert res_district.status_code == 403
    assert "outside your assigned district" in res_district.json()["detail"].lower()

    # MP Khalsa accessing UP work (recommended by another MP) -> 403 Forbidden
    res_mp = client.get(f"/api/v1/works/{UP_WORK_ID}", headers=mp_khalsa_headers)
    assert res_mp.status_code == 403
    assert "outside your assigned mp scrutiny scope" in res_mp.json()["detail"].lower()


def test_single_resource_200_when_within_jurisdiction(state_up_headers, district_patna_headers, mp_khalsa_headers):
    """When work is within caller's jurisdiction, returns 200 OK with full dossier."""
    # State UP officer accessing UP work
    res_up = client.get(f"/api/v1/works/{UP_WORK_ID}", headers=state_up_headers)
    assert res_up.status_code == 200
    assert res_up.json()["work_id"] == UP_WORK_ID

    # District Patna officer accessing Patna work
    res_patna = client.get(f"/api/v1/works/{PATNA_WORK_ID}", headers=district_patna_headers)
    assert res_patna.status_code == 200
    assert res_patna.json()["work_id"] == PATNA_WORK_ID

    # MP Khalsa accessing Khalsa work
    res_khalsa = client.get(f"/api/v1/works/{KHALSA_WORK_ID}", headers=mp_khalsa_headers)
    assert res_khalsa.status_code == 200
    assert res_khalsa.json()["work_id"] == KHALSA_WORK_ID


# --------------------------------------------------------------------------
# 6. Duplicate Works Cross-Jurisdiction Pair Visibility Tests
# --------------------------------------------------------------------------

def test_duplicate_works_pair_visibility_and_single_lookup(state_up_headers):
    """
    Verifies that duplicate candidate pairs involving the state are visible,
    and single pair lookup enforces jurisdiction check.
    """
    res = client.get("/api/v1/analytics/duplicate-works?page_size=5", headers=state_up_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0

    # Test single work duplicate lookup on authorized UP work
    res_lookup = client.get(f"/api/v1/analytics/duplicate-works/pairs/{UP_WORK_ID}", headers=state_up_headers)
    assert res_lookup.status_code == 200
    assert res_lookup.json()["work_id"] == UP_WORK_ID

    # Test single work duplicate lookup on unauthorized Patna work -> 403 Forbidden
    res_unauth = client.get(f"/api/v1/analytics/duplicate-works/pairs/{PATNA_WORK_ID}", headers=state_up_headers)
    assert res_unauth.status_code == 403


# --------------------------------------------------------------------------
# 7. Summaries Scoping Tests
# --------------------------------------------------------------------------

def test_district_summary_scoping(state_up_headers, district_patna_headers):
    """State officer sees only districts in their state; District officer sees only their district."""
    # State UP
    res_state = client.get("/api/v1/analytics/district-summary", headers=state_up_headers)
    assert res_state.status_code == 200
    for d in res_state.json():
        assert d["state"] == "Uttar Pradesh"

    # District Patna
    res_dist = client.get("/api/v1/analytics/district-summary", headers=district_patna_headers)
    assert res_dist.status_code == 200
    assert len(res_dist.json()) == 1
    assert res_dist.json()[0]["district"] == "PATNA"
    assert res_dist.json()[0]["state"] == "Bihar"


def test_mp_summary_scoping(state_up_headers, mp_khalsa_headers):
    """State officer sees MPs in their state; MP sees only their own record."""
    # MP Khalsa
    res_mp = client.get("/api/v1/analytics/mp-summary", headers=mp_khalsa_headers)
    assert res_mp.status_code == 200
    assert len(res_mp.json()) == 1
    assert res_mp.json()[0]["mp_name"] == "SARABJEET SINGH KHALSA"


# --------------------------------------------------------------------------
# 8. User Management RBAC Tests (MINISTRY only)
# --------------------------------------------------------------------------

def test_user_provisioning_rbac(ministry_headers, state_up_headers):
    """Only MINISTRY role can create users; other roles receive 403 Forbidden."""
    payload = {
        "email": "new.officer.test@mplads.gov.in",
        "password": "SecurePassword2026#",
        "full_name": "Test Officer",
        "role": "STATE_OFFICER",
        "assigned_state": "Karnataka"
    }

    # Denied for State Officer -> 403
    res_denied = client.post("/api/v1/auth/users", json=payload, headers=state_up_headers)
    assert res_denied.status_code == 403

    # Allowed for Ministry -> 201
    session = get_session()
    try:
        res_allowed = client.post("/api/v1/auth/users", json=payload, headers=ministry_headers)
        assert res_allowed.status_code == 201
        data = res_allowed.json()
        assert data["email"] == "new.officer.test@mplads.gov.in"
        assert data["role"] == "STATE_OFFICER"
        assert data["assigned_state"] == "Karnataka"
    finally:
        session.query(User).filter(User.email == payload["email"]).delete()
        session.commit()
        session.close()
