import os
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import (
    Base, Work, CostAnomalyResult, DuplicateWorkResult, 
    FundExpenditureResult, DelayResult, User
)
from database.seed_users import DEMO_USERS, hash_seed_password

def get_supabase_direct_engine():
    """Gets direct PostgreSQL engine using DIRECT_URL or DATABASE_URL from .env."""
    env_path = root_dir / ".env"
    direct_url = None
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DIRECT_URL="):
                    direct_url = line.split("=", 1)[1].strip().strip('"')
                elif not direct_url and line.startswith("DATABASE_URL="):
                    direct_url = line.split("=", 1)[1].strip().strip('"')

    if not direct_url or "[YOUR-PASSWORD]" in direct_url or "YOUR_NEW_PASSWORD" in direct_url:
        print("[ERROR] Supabase database password is not set in .env file.")
        print("Please update DIRECT_URL in .env with your actual Supabase database password.")
        sys.exit(1)

    # Clean pgbouncer parameter for direct migration engine if present
    if "?pgbouncer=true" in direct_url:
        direct_url = direct_url.replace("?pgbouncer=true", "")

    print(f"Connecting to Supabase PostgreSQL...")
    return create_engine(direct_url, pool_pre_ping=True)

def populate_supabase():
    t0 = time.time()
    engine = get_supabase_direct_engine()
    
    print("\n--- 1. Resetting & Creating Schema Tables in Supabase Cloud ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] Schema tables initialized in Supabase Cloud.")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # 2. Master Works
        print("\n--- 2. Populating Master Works (190,942 rows) into Supabase Cloud ---")
        df_works = pd.read_parquet("data/features/shared/canonical_works.parquet")
        df_works["work_id"] = df_works["work_id"].astype(str).str.strip()
        df_works["state"] = df_works["state"].fillna("Unknown")
        df_works["district"] = df_works["district"].fillna("Unknown")
        df_works["house"] = df_works["house"].fillna("Lok Sabha")
        df_works["sanction_amount"] = pd.to_numeric(df_works["sanction_amount"], errors="coerce")
        df_works["amount_disbursed"] = pd.to_numeric(df_works["amount_disbursed"], errors="coerce")
        df_works["is_completed_flag"] = df_works["is_completed_flag"].fillna(False).astype(bool)

        for dcol in ["sanction_date", "recommended_date", "completion_date"]:
            df_works[dcol] = pd.to_datetime(df_works[dcol], errors="coerce").dt.date

        works_objs = []
        for _, r in df_works.iterrows():
            works_objs.append(Work(
                work_id=r["work_id"],
                house=r.get("house"),
                state=r["state"],
                district=r["district"],
                ida=r.get("ida"),
                mp_name=r.get("mp_name"),
                constituency=r.get("constituency"),
                constituency_or_term=r.get("constituency_or_term"),
                work_category=r.get("work_category"),
                work_type=r.get("work_type_template"),
                work_description=r.get("work_description"),
                work_status=r.get("work_status"),
                sanction_amount=r["sanction_amount"] if pd.notnull(r["sanction_amount"]) else None,
                sanction_date=r["sanction_date"] if pd.notnull(r["sanction_date"]) else None,
                recommended_date=r["recommended_date"] if pd.notnull(r["recommended_date"]) else None,
                completion_date=r["completion_date"] if pd.notnull(r["completion_date"]) else None,
                amount_disbursed=r["amount_disbursed"] if pd.notnull(r["amount_disbursed"]) else None,
                is_completed_flag=bool(r["is_completed_flag"]),
                image_url=r.get("image_url")
            ))

        # Batch insert with safe payload size (5000 rows)
        batch_size = 5000
        print(f"  Inserting {len(works_objs):,} master works into Supabase Cloud...")
        for i in range(0, len(works_objs), batch_size):
            chunk = works_objs[i:i+batch_size]
            retry = 0
            while retry < 3:
                try:
                    session.bulk_save_objects(chunk)
                    session.commit()
                    break
                except Exception as err:
                    session.rollback()
                    retry += 1
                    print(f"  [RETRY {retry}/3] Batch failed at {i}: {err}")
                    time.sleep(2)

            print(f"  Saved {min(i+batch_size, len(works_objs)):,} / {len(works_objs):,} works...")

        print(f"[OK] Master Works fully updated in Supabase.")

        # 3. Cost Anomaly Results
        print("\n--- 3. Populating Cost Anomaly Results (190,942 rows) ---")
        # 3. Cost Anomaly Results
        print("\n--- 3. Populating Cost Anomaly Results (190,942 rows) ---")
        df_cost = pd.read_parquet("data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet")
        cost_objs = []
        for _, r in df_cost.iterrows():
            cost_objs.append(CostAnomalyResult(
                work_id=str(r["work_id"]).strip(),
                cost_anomaly_score=float(r["cost_anomaly_score"]),
                raw_anomaly_score=float(r["raw_anomaly_score"]) if pd.notnull(r.get("raw_anomaly_score")) else None,
                severity=str(r["severity"]),
                peer_group_used=r.get("peer_group_used"),
                peer_group_level=r.get("peer_group_level"),
                peer_group_size=int(r["peer_group_size"]) if pd.notnull(r.get("peer_group_size")) else None,
                is_data_quality_exception=bool(r.get("is_data_quality_exception", False)),
                explanation=r.get("explanation")
            ))
        for i in range(0, len(cost_objs), 5000):
            session.bulk_save_objects(cost_objs[i:i+5000])
            session.commit()
            print(f"  Saved {min(i+5000, len(cost_objs)):,} / {len(cost_objs):,} Cost Anomaly Results...")
        print(f"[OK] {len(cost_objs):,} Cost Anomaly Results saved to Supabase.")

        # 4. Fund Expenditure Results
        print("\n--- 4. Populating Fund Expenditure Results (190,942 rows) ---")
        df_fund = pd.read_parquet("data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet")
        fund_objs = []
        for _, r in df_fund.iterrows():
            reasons = r.get("anomaly_reasons")
            if isinstance(reasons, (list, np.ndarray)):
                reasons_list = [str(x) for x in reasons if pd.notnull(x)]
            else:
                reasons_list = [str(reasons)] if pd.notnull(reasons) else []

            fund_objs.append(FundExpenditureResult(
                work_id=str(r["work_id"]).strip(),
                fund_anomaly_score=float(r["fund_anomaly_score"]),
                raw_score=float(r["raw_score"]) if pd.notnull(r.get("raw_score")) else None,
                severity=str(r["severity"]),
                audit_category=r.get("audit_category"),
                total_disbursed_amount=float(r["total_disbursed_amount"]) if pd.notnull(r.get("total_disbursed_amount")) else None,
                utilization_ratio=float(r["utilization_ratio"]) if pd.notnull(r.get("utilization_ratio")) else None,
                transaction_count=int(r["transaction_count"]) if pd.notnull(r.get("transaction_count")) else None,
                payment_concentration_hhi=float(r["payment_concentration_hhi"]) if pd.notnull(r.get("payment_concentration_hhi")) else None,
                days_to_first_disbursement=float(r["days_to_first_disbursement"]) if pd.notnull(r.get("days_to_first_disbursement")) else None,
                anomaly_reasons=reasons_list,
                explanation=r.get("explanation")
            ))
        for i in range(0, len(fund_objs), 5000):
            session.bulk_save_objects(fund_objs[i:i+5000])
            session.commit()
            print(f"  Saved {min(i+5000, len(fund_objs)):,} / {len(fund_objs):,} Fund Expenditure Results...")
        print(f"[OK] {len(fund_objs):,} Fund Expenditure Results saved to Supabase.")

        # 5. Delay Results
        print("\n--- 5. Populating Delay SLA Results (190,942 rows) ---")
        df_delay = pd.read_parquet("data/model_outputs/delay_rules/delay_scores.parquet")
        delay_objs = []
        for _, r in df_delay.iterrows():
            delay_types = r.get("active_delay_types")
            if isinstance(delay_types, (list, np.ndarray)):
                types_list = [str(x) for x in delay_types if pd.notnull(x)]
            else:
                types_list = [str(delay_types)] if pd.notnull(delay_types) else []

            delay_objs.append(DelayResult(
                work_id=str(r["work_id"]).strip(),
                delay_score=float(r["delay_score"]),
                severity=str(r["severity"]),
                primary_delay_type=r.get("primary_delay_type"),
                active_delay_types=types_list,
                rec_to_sanc_days=int(r["rec_to_sanc_days"]) if pd.notnull(r.get("rec_to_sanc_days")) else None,
                rec_to_sanc_delay_days=int(r["rec_to_sanc_delay_days"]) if pd.notnull(r.get("rec_to_sanc_delay_days")) else None,
                rec_to_sanc_severity=r.get("rec_to_sanc_severity"),
                sanc_to_comp_days=int(r["sanc_to_comp_days"]) if pd.notnull(r.get("sanc_to_comp_days")) else None,
                sanc_to_comp_delay_days=int(r["sanc_to_comp_delay_days"]) if pd.notnull(r.get("sanc_to_comp_delay_days")) else None,
                sanc_to_comp_severity=r.get("sanc_to_comp_severity"),
                explanation=r.get("explanation")
            ))
        for i in range(0, len(delay_objs), 5000):
            session.bulk_save_objects(delay_objs[i:i+5000])
            session.commit()
            print(f"  Saved {min(i+5000, len(delay_objs)):,} / {len(delay_objs):,} Delay SLA Results...")
        print(f"[OK] {len(delay_objs):,} Delay SLA Results saved to Supabase.")

        # 6. Duplicate Work Pairs
        print("\n--- 6. Populating Top Duplicate Candidate Pairs ---")
        df_dup = pd.read_parquet("data/model_outputs/duplicate_work/duplicate_scores.parquet")
        dup_objs = []
        for idx, (_, r) in enumerate(df_dup.iterrows(), 1):
            dup_objs.append(DuplicateWorkResult(
                id=idx,
                work_id_1=str(r["work_id_1"]).strip(),
                work_id_2=str(r["work_id_2"]).strip(),
                duplicate_score=float(r["duplicate_score"]),
                severity=str(r["severity"]),
                confidence=float(r["confidence"]) if pd.notnull(r.get("confidence")) else None,
                semantic_similarity=float(r["semantic_similarity"]) if pd.notnull(r.get("semantic_similarity")) else None,
                structural_score=float(r["structural_score"]) if pd.notnull(r.get("structural_score")) else None,
                amount_similarity=float(r["amount_similarity"]) if pd.notnull(r.get("amount_similarity")) else None,
                date_proximity=float(r["date_proximity"]) if pd.notnull(r.get("date_proximity")) else None,
                days_diff=int(r["days_diff"]) if pd.notnull(r.get("days_diff")) else None,
                is_same_mp=bool(r["is_same_mp"]) if pd.notnull(r.get("is_same_mp")) else None,
                is_same_constituency=bool(r["is_same_constituency"]) if pd.notnull(r.get("is_same_constituency")) else None,
                explanation=r.get("explanation")
            ))
        for i in range(0, len(dup_objs), 5000):
            session.bulk_save_objects(dup_objs[i:i+5000])
            session.commit()
            print(f"  Saved {min(i+5000, len(dup_objs)):,} / {len(dup_objs):,} Duplicate Candidate Pairs...")
        print(f"[OK] {len(dup_objs):,} Duplicate Candidate Pairs saved to Supabase.")

        # 7. Users
        print("\n--- 7. Seeding Stakeholder Users ---")
        hashed_pw = hash_seed_password("Mplads@Demo2026#")
        for u in DEMO_USERS:
            existing_user = session.query(User).filter(User.email == u["email"]).first()
            if not existing_user:
                session.add(User(
                    email=u["email"],
                    hashed_password=hashed_pw,
                    full_name=u["full_name"],
                    role=u["role"],
                    assigned_state=u["assigned_state"],
                    assigned_district=u["assigned_district"],
                    assigned_mp_name=u["assigned_mp_name"],
                    is_active=True
                ))
        session.commit()
        print("[OK] Stakeholder accounts seeded in Supabase.")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Ingestion failed: {e}")
        raise e
    finally:
        session.close()

    print("\n======================================================================")
    print(f"SUPABASE CLOUD BULK POPULATION COMPLETE IN {time.time()-t0:.2f}s")
    print("======================================================================")

if __name__ == "__main__":
    populate_supabase()
