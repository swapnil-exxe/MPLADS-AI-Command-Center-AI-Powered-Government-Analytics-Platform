import os
import sys
from pathlib import Path
import bcrypt
from sqlalchemy.orm import Session

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from database.connection import get_engine, get_session
from database.models import Base, User
from api.config import settings

DEMO_USERS = [
    {
        "email": "ministry@mplads.gov.in",
        "full_name": "Central MoSPI Administrator",
        "role": "MINISTRY",
        "assigned_state": None,
        "assigned_district": None,
        "assigned_mp_name": None,
    },
    {
        "email": "state.up@mplads.gov.in",
        "full_name": "State Nodal Officer (Uttar Pradesh)",
        "role": "STATE_OFFICER",
        "assigned_state": "Uttar Pradesh",
        "assigned_district": None,
        "assigned_mp_name": None,
    },
    {
        "email": "district.patna@mplads.gov.in",
        "full_name": "District Planning Officer (Patna, Bihar)",
        "role": "DISTRICT_OFFICER",
        "assigned_state": "Bihar",
        "assigned_district": "PATNA",
        "assigned_mp_name": None,
    },
    {
        "email": "mp.khalsa@mplads.gov.in",
        "full_name": "Sarabjeet Singh Khalsa (MP, Faridkot)",
        "role": "MP",
        "assigned_state": None,
        "assigned_district": None,
        "assigned_mp_name": "SARABJEET SINGH KHALSA",
    },
]


def hash_seed_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def seed_stakeholders():
    """Create users table and upsert the 4 canonical stakeholder demo accounts."""
    engine = get_engine()
    print("=" * 70)
    print("MPLADS PLATFORM: Seeding Stakeholder Demo Accounts (Phase 6.3)")
    print("=" * 70)

    # Ensure table exists
    print("Ensuring 'users' table exists in database...")
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    print("[OK] 'users' table checked/created.")

    password = settings.DEMO_SEED_PASSWORD
    if not password:
        password = os.getenv("DEMO_SEED_PASSWORD", "Mplads@Demo2026#")

    hashed_pw = hash_seed_password(password)

    session: Session = get_session()
    try:
        for user_data in DEMO_USERS:
            existing = session.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                existing.full_name = user_data["full_name"]
                existing.role = user_data["role"]
                existing.assigned_state = user_data["assigned_state"]
                existing.assigned_district = user_data["assigned_district"]
                existing.assigned_mp_name = user_data["assigned_mp_name"]
                existing.hashed_password = hashed_pw
                existing.is_active = True
                print(f" [UPDATED] {user_data['role']:<16} | {user_data['email']:<30} | {user_data['full_name']}")
            else:
                new_user = User(
                    email=user_data["email"],
                    hashed_password=hashed_pw,
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    assigned_state=user_data["assigned_state"],
                    assigned_district=user_data["assigned_district"],
                    assigned_mp_name=user_data["assigned_mp_name"],
                    is_active=True,
                )
                session.add(new_user)
                print(f" [CREATED] {user_data['role']:<16} | {user_data['email']:<30} | {user_data['full_name']}")

        session.commit()
        print("-" * 70)
        print("All 4 stakeholder demo accounts successfully seeded into Supabase!")
        print(f"Standard Demo Password: {password} (hashed with bcrypt, 12 rounds)")
        print("=" * 70)
    except Exception as e:
        session.rollback()
        print(f"Error seeding demo stakeholders: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_stakeholders()
