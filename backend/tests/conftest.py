import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.connection import get_session
from database.models import User
from api.auth.security import create_access_token


@pytest.fixture(scope="session")
def client():
    """Unauthenticated TestClient fixture."""
    return TestClient(app)


@pytest.fixture(scope="session")
def users_cache():
    """Loads users once for generating test tokens."""
    session = get_session()
    try:
        users = {u.email: u for u in session.query(User).all()}
        return users
    finally:
        session.close()


def _get_token_for(email: str, users_cache: dict) -> str:
    user = users_cache.get(email)
    if not user:
        session = get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
        finally:
            session.close()
    if not user:
        raise ValueError(f"User '{email}' not found in database. Run seed_users.py first.")

    claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "state": user.assigned_state,
        "district": user.assigned_district,
        "mp_name": user.assigned_mp_name,
    }
    return create_access_token(claims)


@pytest.fixture(scope="session")
def ministry_headers(users_cache):
    """Authorization header with Ministry (unrestricted) access token."""
    token = _get_token_for("ministry@mplads.gov.in", users_cache)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def state_up_headers(users_cache):
    """Authorization header with State Nodal Officer (Uttar Pradesh) access token."""
    token = _get_token_for("state.up@mplads.gov.in", users_cache)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def district_patna_headers(users_cache):
    """Authorization header with District Officer (Patna, Bihar) access token."""
    token = _get_token_for("district.patna@mplads.gov.in", users_cache)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def mp_khalsa_headers(users_cache):
    """Authorization header with MP Sarabjeet Singh Khalsa access token."""
    token = _get_token_for("mp.khalsa@mplads.gov.in", users_cache)
    return {"Authorization": f"Bearer {token}"}
