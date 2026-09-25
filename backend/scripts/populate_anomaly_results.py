import os
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy.orm import sessionmaker
from database.connection import get_engine
from database.models import (
    Base, Work, CostAnomalyResult, DuplicateWorkResult, 
    FundExpenditureResult, DelayResult, User
)
from database.seed_users import DEMO_USERS, hash_seed_password

def populate_anomaly_tables():
    t0 = time.time()
    engine = get_engine()
    
    print("--- 1. Creating Table Schemas in Supabase PostgreSQL ---", flush=True)
    Base.metadata.create_all(bind=engine)
    print("[OK] Table schemas created/verified.", flush=True)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        print("--- Reading local canonical_works.parquet for valid work_ids and prefix_map ---", flush=True)
        df_works = pd.read_parquet("data/features/shared/canonical_works.parquet")
        valid_work_ids = set(df_works["work_id"].astype(str).str.strip())
        
        # Build prefix map for matching base work_id prefixes
        prefix_map = {}
        for w in valid_work_ids:
            prefix_map[w] = w
            base = w.split("-")[0]
            prefix_map[base] = w

        print(f"Total valid work_ids loaded: {len(valid_work_ids):,}", flush=True)

        # 1. Cost Anomaly Results
        print("\n--- 2. Populating Cost Anomaly Results ---", flush=True)
        existing_cost = session.query(CostAnomalyResult).count()
        if existing_cost == 0:
            df_cost = pd.read_parquet("data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet")
            cost_objs = []
            seen = set()
            for _, r in df_cost.iterrows():
                raw_w = str(r["work_id"]).strip()
                w_id = prefix_map.get(raw_w) or prefix_map.get(raw_w.split("-")[0])
                if w_id and w_id not in seen:
                    seen.add(w_id)
                    cost_objs.append(CostAnomalyResult(
                        work_id=w_id,
                        cost_anomaly_score=float(r["cost_anomaly_score"]),
                        raw_anomaly_score=float(r["raw_anomaly_score"]) if pd.notnull(r.get("raw_anomaly_score")) else None,
                        severity=str(r["severity"]),
                        peer_group_used=r.get("peer_group_used"),
                        peer_group_level=r.get("peer_group_level"),
                        peer_group_size=int(r["peer_group_size"]) if pd.notnull(r.get("peer_group_size")) else None,
                        is_data_quality_exception=bool(r.get("is_data_quality_exception", False)),
                        explanation=r.get("explanation")
                    ))
            batch_size = 5000
            for i in range(0, len(cost_objs), batch_size):
                session.bulk_save_objects(cost_objs[i:i+batch_size])
                session.commit()
                print(f"  Saved {min(i+batch_size, len(cost_objs)):,} / {len(cost_objs):,} Cost Anomaly Results...", flush=True)
            print(f"[OK] {len(cost_objs):,} Cost Anomaly Results saved.", flush=True)
        else:
            print(f"[INFO] cost_anomaly_results already contains {existing_cost:,} rows.", flush=True)

        # 2. Fund Expenditure Results
        print("\n--- 3. Populating Fund Expenditure Results ---", flush=True)
        existing_fund = session.query(FundExpenditureResult).count()
        if existing_fund == 0:
            df_fund = pd.read_parquet("data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet")
            fund_objs = []
            seen = set()
            for _, r in df_fund.iterrows():
                raw_w = str(r["work_id"]).strip()
                w_id = prefix_map.get(raw_w) or prefix_map.get(raw_w.split("-")[0])
                if w_id and w_id not in seen:
                    seen.add(w_id)
                    reasons = r.get("anomaly_reasons")
                    if isinstance(reasons, (list, np.ndarray)):
                        reasons_list = [str(x) for x in reasons if pd.notnull(x)]
                    else:
                        reasons_list = [str(reasons)] if pd.notnull(reasons) else []

                    fund_objs.append(FundExpenditureResult(
                        work_id=w_id,
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
            batch_size = 5000
            for i in range(0, len(fund_objs), batch_size):
                session.bulk_save_objects(fund_objs[i:i+batch_size])
                session.commit()
                print(f"  Saved {min(i+batch_size, len(fund_objs)):,} / {len(fund_objs):,} Fund Expenditure Results...", flush=True)
            print(f"[OK] {len(fund_objs):,} Fund Expenditure Results saved.", flush=True)
        else:
            print(f"[INFO] fund_expenditure_results already contains {existing_fund:,} rows.", flush=True)

        # 3. Delay Results
        print("\n--- 4. Populating Delay SLA Results ---", flush=True)
        existing_delay = session.query(DelayResult).count()
        if existing_delay == 0:
            df_delay = pd.read_parquet("data/model_outputs/delay_rules/delay_scores.parquet")
            delay_objs = []
            seen = set()
            for _, r in df_delay.iterrows():
                raw_w = str(r["work_id"]).strip()
                w_id = prefix_map.get(raw_w) or prefix_map.get(raw_w.split("-")[0])
                if w_id and w_id not in seen:
                    seen.add(w_id)
                    delay_types = r.get("active_delay_types")
                    if isinstance(delay_types, (list, np.ndarray)):
                        types_list = [str(x) for x in delay_types if pd.notnull(x)]
                    else:
                        types_list = [str(delay_types)] if pd.notnull(delay_types) else []

                    delay_objs.append(DelayResult(
                        work_id=w_id,
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
            batch_size = 5000
            for i in range(0, len(delay_objs), batch_size):
                session.bulk_save_objects(delay_objs[i:i+batch_size])
                session.commit()
                print(f"  Saved {min(i+batch_size, len(delay_objs)):,} / {len(delay_objs):,} Delay SLA Results...", flush=True)
            print(f"[OK] {len(delay_objs):,} Delay SLA Results saved.", flush=True)
        else:
            print(f"[INFO] delay_results already contains {existing_delay:,} rows.", flush=True)

        # 4. Duplicate Work Pairs
        print("\n--- 5. Populating Duplicate Candidate Pairs ---", flush=True)
        existing_dup = session.query(DuplicateWorkResult).count()
        if existing_dup == 0:
            df_dup = pd.read_parquet("data/model_outputs/duplicate_work/duplicate_scores.parquet")
            dup_objs = []
            seen_pairs = set()
            idx = 1
            for _, r in df_dup.iterrows():
                raw_w1 = str(r["work_id_1"]).strip()
                raw_w2 = str(r["work_id_2"]).strip()
                w1 = prefix_map.get(raw_w1) or prefix_map.get(raw_w1.split("-")[0])
                w2 = prefix_map.get(raw_w2) or prefix_map.get(raw_w2.split("-")[0])
                if w1 and w2 and w1 != w2:
                    pair_key = (min(w1, w2), max(w1, w2))
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        dup_objs.append(DuplicateWorkResult(
                            id=idx,
                            work_id_1=w1,
                            work_id_2=w2,
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
                        idx += 1
            batch_size = 5000
            for i in range(0, len(dup_objs), batch_size):
                session.bulk_save_objects(dup_objs[i:i+batch_size])
                session.commit()
                print(f"  Saved {min(i+batch_size, len(dup_objs)):,} / {len(dup_objs):,} Duplicate Candidate Pairs...", flush=True)
            print(f"[OK] {len(dup_objs):,} Duplicate Candidate Pairs saved.", flush=True)
        else:
            print(f"[INFO] duplicate_work_results already contains {existing_dup:,} rows.", flush=True)

        # 5. Users
        print("\n--- 6. Seeding Users ---", flush=True)
        existing_users = session.query(User).count()
        if existing_users == 0:
            hashed_pw = hash_seed_password("Mplads@Demo2026#")
            for u in DEMO_USERS:
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
            print("[OK] Stakeholder accounts seeded.", flush=True)
        else:
            print(f"[INFO] users table already contains {existing_users:,} rows.", flush=True)

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Ingestion failed: {e}", flush=True)
        raise e
    finally:
        session.close()

    print("\n======================================================================", flush=True)
    print(f"SUPABASE ANOMALY POPULATION COMPLETE IN {time.time()-t0:.2f}s", flush=True)
    print("======================================================================", flush=True)

if __name__ == "__main__":
    populate_anomaly_tables()
