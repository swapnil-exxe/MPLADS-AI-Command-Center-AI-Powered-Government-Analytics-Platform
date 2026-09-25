import os
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from database.connection import get_engine
from database.models import Base
from database.seed_users import DEMO_USERS, hash_seed_password

def populate_all():
    t0 = time.time()
    engine = get_engine()
    
    print("--- 1. Initializing Schemas in Supabase PostgreSQL ---", flush=True)
    Base.metadata.create_all(bind=engine)
    print("[OK] Schema verified.", flush=True)

    with engine.connect() as conn:
        print("--- 2. Building Work ID Mapping ---", flush=True)
        works_rows = conn.execute(text("SELECT work_id FROM works")).fetchall()
        valid_work_ids = set(r[0] for r in works_rows)
        prefix_to_full = {w.split('-')[0]: w for w in valid_work_ids}
        for w in valid_work_ids:
            prefix_to_full[w] = w
        print(f"Loaded {len(valid_work_ids):,} valid works from Supabase database.", flush=True)

        # 1. Cost Anomaly Results
        print("\n--- 3. Cost Anomaly Results ---", flush=True)
        cost_cnt = conn.execute(text("SELECT COUNT(*) FROM cost_anomaly_results")).scalar()
        if cost_cnt < 98000:
            print("Populating cost_anomaly_results...", flush=True)
            df_cost = pd.read_parquet("data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet")
            df_cost["canonical_work_id"] = df_cost["work_id"].astype(str).str.strip().map(lambda x: prefix_to_full.get(x) or prefix_to_full.get(x.split('-')[0]))
            df_cost = df_cost.dropna(subset=["canonical_work_id"]).drop_duplicates(subset=["canonical_work_id"])
            
            insert_cost = text("""
                INSERT INTO cost_anomaly_results (
                    work_id, cost_anomaly_score, raw_anomaly_score, severity, 
                    peer_group_used, peer_group_level, peer_group_size, 
                    is_data_quality_exception, explanation
                ) VALUES (
                    :work_id, :cost_anomaly_score, :raw_anomaly_score, :severity, 
                    :peer_group_used, :peer_group_level, :peer_group_size, 
                    :is_data_quality_exception, :explanation
                ) ON CONFLICT (work_id) DO NOTHING
            """)

            cost_records = []
            for _, r in df_cost.iterrows():
                cost_records.append({
                    "work_id": r["canonical_work_id"],
                    "cost_anomaly_score": float(r["cost_anomaly_score"]),
                    "raw_anomaly_score": float(r["raw_anomaly_score"]) if pd.notnull(r.get("raw_anomaly_score")) else None,
                    "severity": str(r["severity"]),
                    "peer_group_used": r.get("peer_group_used") if pd.notnull(r.get("peer_group_used")) else None,
                    "peer_group_level": r.get("peer_group_level") if pd.notnull(r.get("peer_group_level")) else None,
                    "peer_group_size": int(r["peer_group_size"]) if pd.notnull(r.get("peer_group_size")) else None,
                    "is_data_quality_exception": bool(r.get("is_data_quality_exception", False)),
                    "explanation": r.get("explanation") if pd.notnull(r.get("explanation")) else None
                })
            batch_size = 5000
            for i in range(0, len(cost_records), batch_size):
                conn.execute(insert_cost, cost_records[i:i+batch_size])
                conn.commit()
                print(f"  Cost anomalies: {min(i+batch_size, len(cost_records)):,} / {len(cost_records):,}", flush=True)
            print("[OK] cost_anomaly_results populated.", flush=True)
        else:
            print(f"[OK] cost_anomaly_results already populated ({cost_cnt:,} rows).", flush=True)

        # 2. Fund Expenditure Results
        print("\n--- 4. Fund Expenditure Results ---", flush=True)
        fund_cnt = conn.execute(text("SELECT COUNT(*) FROM fund_expenditure_results")).scalar()
        if fund_cnt < 98000:
            print("Populating fund_expenditure_results...", flush=True)
            df_fund = pd.read_parquet("data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet")
            df_fund["canonical_work_id"] = df_fund["work_id"].astype(str).str.strip().map(lambda x: prefix_to_full.get(x) or prefix_to_full.get(x.split('-')[0]))
            df_fund = df_fund.dropna(subset=["canonical_work_id"]).drop_duplicates(subset=["canonical_work_id"])
            
            insert_fund = text("""
                INSERT INTO fund_expenditure_results (
                    work_id, fund_anomaly_score, raw_score, severity, audit_category, 
                    total_disbursed_amount, utilization_ratio, transaction_count, 
                    payment_concentration_hhi, days_to_first_disbursement, anomaly_reasons, explanation
                ) VALUES (
                    :work_id, :fund_anomaly_score, :raw_score, :severity, :audit_category, 
                    :total_disbursed_amount, :utilization_ratio, :transaction_count, 
                    :payment_concentration_hhi, :days_to_first_disbursement, :anomaly_reasons, :explanation
                ) ON CONFLICT (work_id) DO NOTHING
            """)

            fund_records = []
            for _, r in df_fund.iterrows():
                reasons = r.get("anomaly_reasons")
                if isinstance(reasons, list) or hasattr(reasons, "__iter__") and not isinstance(reasons, str):
                    reasons_list = [str(x) for x in reasons if pd.notnull(x)]
                else:
                    reasons_list = [str(reasons)] if pd.notnull(reasons) else []

                fund_records.append({
                    "work_id": r["canonical_work_id"],
                    "fund_anomaly_score": float(r["fund_anomaly_score"]),
                    "raw_score": float(r["raw_score"]) if pd.notnull(r.get("raw_score")) else None,
                    "severity": str(r["severity"]),
                    "audit_category": r.get("audit_category") if pd.notnull(r.get("audit_category")) else None,
                    "total_disbursed_amount": float(r["total_disbursed_amount"]) if pd.notnull(r.get("total_disbursed_amount")) else None,
                    "utilization_ratio": float(r["utilization_ratio"]) if pd.notnull(r.get("utilization_ratio")) else None,
                    "transaction_count": int(r["transaction_count"]) if pd.notnull(r.get("transaction_count")) else None,
                    "payment_concentration_hhi": float(r["payment_concentration_hhi"]) if pd.notnull(r.get("payment_concentration_hhi")) else None,
                    "days_to_first_disbursement": float(r["days_to_first_disbursement"]) if pd.notnull(r.get("days_to_first_disbursement")) else None,
                    "anomaly_reasons": reasons_list,
                    "explanation": r.get("explanation") if pd.notnull(r.get("explanation")) else None
                })
            batch_size = 5000
            for i in range(0, len(fund_records), batch_size):
                conn.execute(insert_fund, fund_records[i:i+batch_size])
                conn.commit()
                print(f"  Fund expenditure results: {min(i+batch_size, len(fund_records)):,} / {len(fund_records):,}", flush=True)
            print("[OK] fund_expenditure_results populated.", flush=True)
        else:
            print(f"[OK] fund_expenditure_results already populated ({fund_cnt:,} rows).", flush=True)

        # 3. Delay Results
        print("\n--- 5. Delay Results ---", flush=True)
        delay_cnt = conn.execute(text("SELECT COUNT(*) FROM delay_results")).scalar()
        if delay_cnt < 98000:
            print("Populating delay_results...", flush=True)
            df_delay = pd.read_parquet("data/model_outputs/delay_rules/delay_scores.parquet")
            df_delay["canonical_work_id"] = df_delay["work_id"].astype(str).str.strip().map(lambda x: prefix_to_full.get(x) or prefix_to_full.get(x.split('-')[0]))
            df_delay = df_delay.dropna(subset=["canonical_work_id"]).drop_duplicates(subset=["canonical_work_id"])

            insert_delay = text("""
                INSERT INTO delay_results (
                    work_id, delay_score, severity, primary_delay_type, active_delay_types, 
                    rec_to_sanc_days, rec_to_sanc_delay_days, rec_to_sanc_severity, 
                    sanc_to_comp_days, sanc_to_comp_delay_days, sanc_to_comp_severity, explanation
                ) VALUES (
                    :work_id, :delay_score, :severity, :primary_delay_type, :active_delay_types, 
                    :rec_to_sanc_days, :rec_to_sanc_delay_days, :rec_to_sanc_severity, 
                    :sanc_to_comp_days, :sanc_to_comp_delay_days, :sanc_to_comp_severity, :explanation
                ) ON CONFLICT (work_id) DO NOTHING
            """)

            delay_records = []
            for _, r in df_delay.iterrows():
                delay_types = r.get("active_delay_types")
                if isinstance(delay_types, list) or hasattr(delay_types, "__iter__") and not isinstance(delay_types, str):
                    types_list = [str(x) for x in delay_types if pd.notnull(x)]
                else:
                    types_list = [str(delay_types)] if pd.notnull(delay_types) else []

                delay_records.append({
                    "work_id": r["canonical_work_id"],
                    "delay_score": float(r["delay_score"]),
                    "severity": str(r["severity"]),
                    "primary_delay_type": r.get("primary_delay_type") if pd.notnull(r.get("primary_delay_type")) else None,
                    "active_delay_types": types_list,
                    "rec_to_sanc_days": int(r["rec_to_sanc_days"]) if pd.notnull(r.get("rec_to_sanc_days")) else None,
                    "rec_to_sanc_delay_days": int(r["rec_to_sanc_delay_days"]) if pd.notnull(r.get("rec_to_sanc_delay_days")) else None,
                    "rec_to_sanc_severity": r.get("rec_to_sanc_severity") if pd.notnull(r.get("rec_to_sanc_severity")) else None,
                    "sanc_to_comp_days": int(r["sanc_to_comp_days"]) if pd.notnull(r.get("sanc_to_comp_days")) else None,
                    "sanc_to_comp_delay_days": int(r["sanc_to_comp_delay_days"]) if pd.notnull(r.get("sanc_to_comp_delay_days")) else None,
                    "sanc_to_comp_severity": r.get("sanc_to_comp_severity") if pd.notnull(r.get("sanc_to_comp_severity")) else None,
                    "explanation": r.get("explanation") if pd.notnull(r.get("explanation")) else None
                })
            batch_size = 5000
            for i in range(0, len(delay_records), batch_size):
                conn.execute(insert_delay, delay_records[i:i+batch_size])
                conn.commit()
                print(f"  Delay results: {min(i+batch_size, len(delay_records)):,} / {len(delay_records):,}", flush=True)
            print("[OK] delay_results populated.", flush=True)
        else:
            print(f"[OK] delay_results already populated ({delay_cnt:,} rows).", flush=True)

        # 4. Duplicate Work Results
        print("\n--- 6. Duplicate Work Results ---", flush=True)
        dup_cnt = conn.execute(text("SELECT COUNT(*) FROM duplicate_work_results")).scalar()
        if dup_cnt < 10000:
            print("Populating duplicate_work_results...", flush=True)
            df_dup = pd.read_parquet("data/model_outputs/duplicate_work/duplicate_scores.parquet")
            df_dup["w1"] = df_dup["work_id_1"].astype(str).str.strip().map(lambda x: prefix_to_full.get(x) or prefix_to_full.get(x.split('-')[0]))
            df_dup["w2"] = df_dup["work_id_2"].astype(str).str.strip().map(lambda x: prefix_to_full.get(x) or prefix_to_full.get(x.split('-')[0]))
            df_dup = df_dup.dropna(subset=["w1", "w2"])
            df_dup = df_dup[df_dup["w1"] != df_dup["w2"]]

            insert_dup = text("""
                INSERT INTO duplicate_work_results (
                    id, work_id_1, work_id_2, duplicate_score, severity, confidence, 
                    semantic_similarity, structural_score, amount_similarity, 
                    date_proximity, days_diff, is_same_mp, is_same_constituency, explanation
                ) VALUES (
                    :id, :work_id_1, :work_id_2, :duplicate_score, :severity, :confidence, 
                    :semantic_similarity, :structural_score, :amount_similarity, 
                    :date_proximity, :days_diff, :is_same_mp, :is_same_constituency, :explanation
                ) ON CONFLICT (work_id_1, work_id_2) DO NOTHING
            """)

            dup_records = []
            seen_pairs = set()
            idx = 1
            for _, r in df_dup.iterrows():
                w1, w2 = r["w1"], r["w2"]
                pair_key = (min(w1, w2), max(w1, w2))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    dup_records.append({
                        "id": idx,
                        "work_id_1": w1,
                        "work_id_2": w2,
                        "duplicate_score": float(r["duplicate_score"]),
                        "severity": str(r["severity"]),
                        "confidence": float(r["confidence"]) if pd.notnull(r.get("confidence")) else None,
                        "semantic_similarity": float(r["semantic_similarity"]) if pd.notnull(r.get("semantic_similarity")) else None,
                        "structural_score": float(r["structural_score"]) if pd.notnull(r.get("structural_score")) else None,
                        "amount_similarity": float(r["amount_similarity"]) if pd.notnull(r.get("amount_similarity")) else None,
                        "date_proximity": float(r["date_proximity"]) if pd.notnull(r.get("date_proximity")) else None,
                        "days_diff": int(r["days_diff"]) if pd.notnull(r.get("days_diff")) else None,
                        "is_same_mp": bool(r["is_same_mp"]) if pd.notnull(r.get("is_same_mp")) else None,
                        "is_same_constituency": bool(r["is_same_constituency"]) if pd.notnull(r.get("is_same_constituency")) else None,
                        "explanation": r.get("explanation") if pd.notnull(r.get("explanation")) else None
                    })
                    idx += 1

            batch_size = 5000
            for i in range(0, len(dup_records), batch_size):
                conn.execute(insert_dup, dup_records[i:i+batch_size])
                conn.commit()
                print(f"  Duplicate candidate pairs: {min(i+batch_size, len(dup_records)):,} / {len(dup_records):,}", flush=True)
            print("[OK] duplicate_work_results populated.", flush=True)
        else:
            print(f"[OK] duplicate_work_results already populated ({dup_cnt:,} rows).", flush=True)

        # 5. Users
        print("\n--- 7. Seeding Demo Users ---", flush=True)
        users_cnt = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if users_cnt == 0:
            insert_user = text("""
                INSERT INTO users (
                    email, hashed_password, full_name, role, 
                    assigned_state, assigned_district, assigned_mp_name, is_active
                ) VALUES (
                    :email, :hashed_password, :full_name, :role, 
                    :assigned_state, :assigned_district, :assigned_mp_name, :is_active
                ) ON CONFLICT (email) DO NOTHING
            """)
            hashed_pw = hash_seed_password("Mplads@Demo2026#")
            user_records = []
            for u in DEMO_USERS:
                user_records.append({
                    "email": u["email"],
                    "hashed_password": hashed_pw,
                    "full_name": u["full_name"],
                    "role": u["role"],
                    "assigned_state": u["assigned_state"],
                    "assigned_district": u["assigned_district"],
                    "assigned_mp_name": u["assigned_mp_name"],
                    "is_active": True
                })
            conn.execute(insert_user, user_records)
            conn.commit()
            print("[OK] Stakeholder users populated.", flush=True)
        else:
            print(f"[OK] users already populated ({users_cnt:,} rows).", flush=True)

    print("\n======================================================================", flush=True)
    print(f"SUPABASE FULL DATASET POPULATION COMPLETED IN {time.time()-t0:.2f}s", flush=True)
    print("======================================================================", flush=True)

if __name__ == "__main__":
    populate_all()
