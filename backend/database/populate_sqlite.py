import os
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import get_engine, get_session
from database.models import (
    Base, Work, CostAnomalyResult, DuplicateWorkResult, 
    FundExpenditureResult, DelayResult, User
)
from database.seed_users import seed_stakeholders

def populate_database():
    """Populates SQLite database with canonical works and all 4 model output datasets."""
    t0 = time.time()
    print("======================================================================")
    print("STARTING BULK DATASET POPULATION FOR LOCAL SQLITE (190,942 WORKS)")
    print("======================================================================")

    # Force recreate tables for clean reset
    sqlite_path = root_dir / "database" / "mplads_master.db"
    if sqlite_path.exists():
        try:
            os.remove(sqlite_path)
            print("[RESET] Removed old SQLite database file.")
        except Exception:
            pass

    engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    
    # 1. Create all tables in database
    print("\n--- 1. Creating Schema Tables ---")
    Base.metadata.create_all(bind=engine)
    print("[OK] Schema tables initialized.")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # 2. Populate Works (190,942 rows)
        print("\n--- 2. Populating Master Works Table (190,942 rows) ---")
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
                house=r["house"],
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

        batch_size = 10000
        for i in range(0, len(works_objs), batch_size):
            session.bulk_save_objects(works_objs[i:i+batch_size])
            session.commit()
            print(f"  Saved {min(i+batch_size, len(works_objs)):,} / {len(works_objs):,} works...")

        print(f"[OK] {len(works_objs):,} Master Works saved.")

        # 3. Populate Cost Anomaly Results (190,942 rows)
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
        for i in range(0, len(cost_objs), 10000):
            session.bulk_save_objects(cost_objs[i:i+10000])
            session.commit()
        print(f"[OK] {len(cost_objs):,} Cost Anomaly Results saved.")

        # 4. Populate Fund Expenditure Results (190,942 rows)
        print("\n--- 4. Populating Fund Expenditure Results (190,942 rows) ---")
        df_fund = pd.read_parquet("data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet")
        
        import re
        work_id_map = {}
        for c_id in df_works["work_id"]:
            m = re.match(r'^(WS/\s*MP\d+/\d{4}-\d{4}/\d+)', str(c_id))
            if m:
                raw_key = re.sub(r'\s+', '', m.group(1))
                work_id_map[raw_key] = str(c_id)

        fund_objs = []
        for _, r in df_fund.iterrows():
            raw_wid = str(r["work_id"]).strip()
            canonical_wid = work_id_map.get(raw_wid, raw_wid)

            reasons = r.get("anomaly_reasons")
            if isinstance(reasons, (list, np.ndarray)):
                reasons_str = ", ".join([str(x) for x in reasons if pd.notnull(x)])
            else:
                reasons_str = str(reasons) if pd.notnull(reasons) else None

            fund_objs.append(FundExpenditureResult(
                work_id=canonical_wid,
                fund_anomaly_score=float(r["fund_anomaly_score"]),
                raw_score=float(r["raw_score"]) if pd.notnull(r.get("raw_score")) else None,
                severity=str(r["severity"]),
                audit_category=r.get("audit_category"),
                total_disbursed_amount=float(r["total_disbursed_amount"]) if pd.notnull(r.get("total_disbursed_amount")) else None,
                utilization_ratio=float(r["utilization_ratio"]) if pd.notnull(r.get("utilization_ratio")) else None,
                transaction_count=int(r["transaction_count"]) if pd.notnull(r.get("transaction_count")) else None,
                payment_concentration_hhi=float(r["payment_concentration_hhi"]) if pd.notnull(r.get("payment_concentration_hhi")) else None,
                days_to_first_disbursement=float(r["days_to_first_disbursement"]) if pd.notnull(r.get("days_to_first_disbursement")) else None,
                explanation=f"{r.get('explanation', '')} Reasons: {reasons_str}" if reasons_str else r.get("explanation")
            ))
        for i in range(0, len(fund_objs), 10000):
            session.bulk_save_objects(fund_objs[i:i+10000])
            session.commit()
        print(f"[OK] {len(fund_objs):,} Fund Expenditure Results saved.")

        # 5. Populate Delay Results (190,942 rows)
        print("\n--- 5. Populating Delay SLA Results (190,942 rows) ---")
        df_delay = pd.read_parquet("data/model_outputs/delay_rules/delay_scores.parquet")
        delay_objs = []
        for _, r in df_delay.iterrows():
            delay_types = r.get("active_delay_types")
            if isinstance(delay_types, (list, np.ndarray)):
                types_str = ", ".join([str(x) for x in delay_types if pd.notnull(x)])
            else:
                types_str = str(delay_types) if pd.notnull(delay_types) else None

            delay_objs.append(DelayResult(
                work_id=str(r["work_id"]).strip(),
                delay_score=float(r["delay_score"]),
                severity=str(r["severity"]),
                primary_delay_type=r.get("primary_delay_type"),
                rec_to_sanc_days=int(r["rec_to_sanc_days"]) if pd.notnull(r.get("rec_to_sanc_days")) else None,
                rec_to_sanc_delay_days=int(r["rec_to_sanc_delay_days"]) if pd.notnull(r.get("rec_to_sanc_delay_days")) else None,
                rec_to_sanc_severity=r.get("rec_to_sanc_severity"),
                sanc_to_comp_days=int(r["sanc_to_comp_days"]) if pd.notnull(r.get("sanc_to_comp_days")) else None,
                sanc_to_comp_delay_days=int(r["sanc_to_comp_delay_days"]) if pd.notnull(r.get("sanc_to_comp_delay_days")) else None,
                sanc_to_comp_severity=r.get("sanc_to_comp_severity"),
                explanation=f"{r.get('explanation', '')} Delay Types: {types_str}" if types_str else r.get("explanation")
            ))
        for i in range(0, len(delay_objs), 10000):
            session.bulk_save_objects(delay_objs[i:i+10000])
            session.commit()
        print(f"[OK] {len(delay_objs):,} Delay SLA Results saved.")

        # 6. Populate Candidate Duplicate Work Pairs
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
        for i in range(0, len(dup_objs), 10000):
            session.bulk_save_objects(dup_objs[i:i+10000])
            session.commit()
        print(f"[OK] {len(dup_objs):,} Duplicate Candidate Pairs saved.")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Ingestion failed: {e}")
        raise e
    finally:
        session.close()

    # 7. Seed Users
    print("\n--- 7. Seeding Stakeholder Demo Accounts ---")
    seed_stakeholders()

    print("\n======================================================================")
    print(f"SQLITE BULK POPULATION COMPLETE IN {time.time()-t0:.2f}s")
    print("======================================================================")

if __name__ == "__main__":
    populate_database()
