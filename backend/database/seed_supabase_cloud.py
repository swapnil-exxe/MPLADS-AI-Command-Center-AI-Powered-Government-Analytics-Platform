import os
import sys
import json
import time
from pathlib import Path
import pandas as pd
import numpy as np
import requests

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from database.seed_users import DEMO_USERS, hash_seed_password

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fcpwrmzviqrhsdgelwmk.supabase.co")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_SECRET_KEY:
    print("[ERROR] SUPABASE_SECRET_KEY environment variable is missing.")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_SECRET_KEY,
    "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def clean_val(val):
    if pd.isna(val) or val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return None
    return val

def upload_batch(endpoint, records, table_name, batch_size=1000):
    total = len(records)
    uploaded = 0
    for i in range(0, total, batch_size):
        chunk = records[i:i+batch_size]
        res = requests.post(endpoint, headers=HEADERS, json=chunk)
        if res.status_code in [200, 201]:
            uploaded += len(chunk)
            if i % 10000 == 0 or uploaded == total:
                print(f"  [{table_name.upper()}] Uploaded {uploaded:,} / {total:,} rows...")
        else:
            print(f"  [ERROR] Table '{table_name}' upload failed at batch {i}: {res.status_code} - {res.text}")
            return False
    print(f"[OK] {table_name} upload complete ({uploaded:,} rows).")
    return True

def seed_supabase_cloud():
    """Pushes canonical works and model anomaly datasets to Supabase Cloud REST API."""
    print("======================================================================")
    print("STARTING SUPABASE CLOUD DATASET INGESTION")
    print(f"Target Instance: {SUPABASE_URL}")
    print("======================================================================")

    # 1. Works Table
    print("\n--- 1. Uploading Master Works (98,825 rows) ---")
    df_works = pd.read_parquet("data/features/shared/canonical_works.parquet")
    df_works["work_id"] = df_works["work_id"].astype(str).str.strip()
    df_works["state"] = df_works["state"].fillna("Unknown")
    df_works["district"] = df_works["district"].fillna("Unknown")
    df_works["house"] = df_works["house"].fillna("Lok Sabha")
    df_works["sanction_amount"] = pd.to_numeric(df_works["sanction_amount"], errors="coerce")
    df_works["amount_disbursed"] = pd.to_numeric(df_works["amount_disbursed"], errors="coerce")
    df_works["is_completed_flag"] = df_works["is_completed_flag"].fillna(False).astype(bool)

    for dcol in ["sanction_date", "recommended_date", "completion_date"]:
        df_works[dcol] = pd.to_datetime(df_works[dcol], errors="coerce").dt.strftime("%Y-%m-%d")

    records = []
    for _, r in df_works.iterrows():
        records.append({
            "work_id": str(r["work_id"]).strip(),
            "house": clean_val(r.get("house")),
            "state": str(r["state"]),
            "district": str(r["district"]),
            "ida": clean_val(r.get("ida")),
            "mp_name": clean_val(r.get("mp_name")),
            "constituency": clean_val(r.get("constituency")),
            "constituency_or_term": clean_val(r.get("constituency_or_term")),
            "work_category": clean_val(r.get("work_category")),
            "work_type": clean_val(r.get("work_type_template")),
            "work_description": clean_val(r.get("work_description")),
            "work_status": clean_val(r.get("work_status")),
            "sanction_amount": float(r["sanction_amount"]) if pd.notnull(r["sanction_amount"]) else None,
            "sanction_date": clean_val(r["sanction_date"]),
            "recommended_date": clean_val(r["recommended_date"]),
            "completion_date": clean_val(r["completion_date"]),
            "amount_disbursed": float(r["amount_disbursed"]) if pd.notnull(r["amount_disbursed"]) else None,
            "is_completed_flag": bool(r["is_completed_flag"]),
            "image_url": clean_val(r.get("image_url"))
        })

    if not upload_batch(f"{SUPABASE_URL}/rest/v1/works", records, "works"):
        return

    # 2. Cost Anomaly Results
    print("\n--- 2. Uploading Cost Anomaly Results (98,825 rows) ---")
    df_cost = pd.read_parquet("data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet")
    cost_records = []
    for _, r in df_cost.iterrows():
        cost_records.append({
            "work_id": str(r["work_id"]).strip(),
            "cost_anomaly_score": float(r["cost_anomaly_score"]),
            "raw_anomaly_score": float(r["raw_anomaly_score"]) if pd.notnull(r.get("raw_anomaly_score")) else None,
            "severity": str(r["severity"]),
            "peer_group_used": clean_val(r.get("peer_group_used")),
            "peer_group_level": clean_val(r.get("peer_group_level")),
            "peer_group_size": int(r["peer_group_size"]) if pd.notnull(r.get("peer_group_size")) else None,
            "is_data_quality_exception": bool(r.get("is_data_quality_exception", False)),
            "explanation": clean_val(r.get("explanation"))
        })
    upload_batch(f"{SUPABASE_URL}/rest/v1/cost_anomaly_results", cost_records, "cost_anomaly_results")

    # 3. Fund Expenditure Results
    print("\n--- 3. Uploading Fund Expenditure Results (98,825 rows) ---")
    df_fund = pd.read_parquet("data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet")
    fund_records = []
    for _, r in df_fund.iterrows():
        reasons = r.get("anomaly_reasons")
        if isinstance(reasons, (list, np.ndarray)):
            reasons_list = [str(x) for x in reasons if pd.notnull(x)]
        else:
            reasons_list = [str(reasons)] if pd.notnull(reasons) else []

        fund_records.append({
            "work_id": str(r["work_id"]).strip(),
            "fund_anomaly_score": float(r["fund_anomaly_score"]),
            "raw_score": float(r["raw_score"]) if pd.notnull(r.get("raw_score")) else None,
            "severity": str(r["severity"]),
            "audit_category": clean_val(r.get("audit_category")),
            "total_disbursed_amount": float(r["total_disbursed_amount"]) if pd.notnull(r.get("total_disbursed_amount")) else None,
            "utilization_ratio": float(r["utilization_ratio"]) if pd.notnull(r.get("utilization_ratio")) else None,
            "transaction_count": int(r["transaction_count"]) if pd.notnull(r.get("transaction_count")) else None,
            "payment_concentration_hhi": float(r["payment_concentration_hhi"]) if pd.notnull(r.get("payment_concentration_hhi")) else None,
            "days_to_first_disbursement": float(r["days_to_first_disbursement"]) if pd.notnull(r.get("days_to_first_disbursement")) else None,
            "anomaly_reasons": reasons_list,
            "explanation": clean_val(r.get("explanation"))
        })
    upload_batch(f"{SUPABASE_URL}/rest/v1/fund_expenditure_results", fund_records, "fund_expenditure_results")

    # 4. Delay SLA Results
    print("\n--- 4. Uploading Delay SLA Results (98,825 rows) ---")
    df_delay = pd.read_parquet("data/model_outputs/delay_rules/delay_scores.parquet")
    delay_records = []
    for _, r in df_delay.iterrows():
        delay_types = r.get("active_delay_types")
        if isinstance(delay_types, (list, np.ndarray)):
            delay_list = [str(x) for x in delay_types if pd.notnull(x)]
        else:
            delay_list = [str(delay_types)] if pd.notnull(delay_types) else []

        delay_records.append({
            "work_id": str(r["work_id"]).strip(),
            "delay_score": float(r["delay_score"]),
            "severity": str(r["severity"]),
            "primary_delay_type": clean_val(r.get("primary_delay_type")),
            "active_delay_types": delay_list,
            "rec_to_sanc_days": int(r["rec_to_sanc_days"]) if pd.notnull(r.get("rec_to_sanc_days")) else None,
            "rec_to_sanc_delay_days": int(r["rec_to_sanc_delay_days"]) if pd.notnull(r.get("rec_to_sanc_delay_days")) else None,
            "rec_to_sanc_severity": clean_val(r.get("rec_to_sanc_severity")),
            "sanc_to_comp_days": int(r["sanc_to_comp_days"]) if pd.notnull(r.get("sanc_to_comp_days")) else None,
            "sanc_to_comp_delay_days": int(r["sanc_to_comp_delay_days"]) if pd.notnull(r.get("sanc_to_comp_delay_days")) else None,
            "sanc_to_comp_severity": clean_val(r.get("sanc_to_comp_severity")),
            "explanation": clean_val(r.get("explanation"))
        })
    upload_batch(f"{SUPABASE_URL}/rest/v1/delay_results", delay_records, "delay_results")

    # 5. Duplicate Work Pairs
    print("\n--- 5. Uploading Duplicate Candidate Pairs (10,000 top pairs) ---")
    df_dup = pd.read_parquet("data/model_outputs/duplicate_work/duplicate_scores.parquet")
    df_top = df_dup[df_dup["duplicate_score"] >= 0.6].head(10000).copy()
    dup_records = []
    for idx, (_, r) in enumerate(df_top.iterrows(), 1):
        dup_records.append({
            "id": idx,
            "work_id_1": str(r["work_id_1"]).strip(),
            "work_id_2": str(r["work_id_2"]).strip(),
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
            "explanation": clean_val(r.get("explanation"))
        })
    upload_batch(f"{SUPABASE_URL}/rest/v1/duplicate_work_results", dup_records, "duplicate_work_results")

    # 6. Users
    print("\n--- 6. Seeding Stakeholder Users ---")
    user_records = []
    for u in DEMO_USERS:
        user_records.append({
            "email": u["email"],
            "hashed_password": hash_seed_password("Mplads@Demo2026#"),
            "full_name": u["full_name"],
            "role": u["role"],
            "assigned_state": u["assigned_state"],
            "assigned_district": u["assigned_district"],
            "assigned_mp_name": u["assigned_mp_name"],
            "is_active": True
        })
    upload_batch(f"{SUPABASE_URL}/rest/v1/users", user_records, "users")

    print("\n======================================================================")
    print("SUPABASE CLOUD DATASET INGESTION COMPLETE")
    print("======================================================================")

if __name__ == "__main__":
    seed_supabase_cloud()
