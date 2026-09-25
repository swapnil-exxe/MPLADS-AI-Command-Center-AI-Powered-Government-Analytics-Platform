import os
import sys
import json
import urllib.request
from pathlib import Path
import pandas as pd

root_dir = Path(__file__).resolve().parent.parent

def run_pipeline_verification():
    print("==================================================")
    print("FINAL DATA VERIFICATION REPORT")
    print("==================================================")

    # 1. Raw Files & Rows
    dataset_dir = root_dir / "dataset"
    raw_files = list(dataset_dir.rglob("*.csv"))
    total_raw_rows = 0
    for f in raw_files:
        try:
            df_r = pd.read_csv(f, encoding="utf-8-sig", low_memory=False)
            total_raw_rows += len(df_r)
        except Exception:
            pass

    print(f"\nRaw files:")
    print(f"{len(raw_files)}")
    print(f"\nRaw rows:")
    print(f"{total_raw_rows:,}")

    # 2. Canonical Works
    canonical_path = root_dir / "data" / "features" / "shared" / "canonical_works.parquet"
    if not canonical_path.exists():
        print("\n[FAIL] Canonical works parquet missing!")
        return False

    df_c = pd.read_parquet(canonical_path)
    tot_works = len(df_c)
    tot_sanc = df_c["sanction_amount"].sum() / 1e7
    tot_disb = df_c["amount_disbursed"].sum() / 1e7
    util_rate = (tot_disb / tot_sanc * 100.0) if tot_sanc > 0 else 0.0

    print(f"\nCanonical works:")
    print(f"{tot_works:,}")
    print(f"\nTotal sanctioned:")
    print(f"₹{tot_sanc:,.2f} Cr")
    print(f"\nTotal disbursed:")
    print(f"₹{tot_disb:,.2f} Cr")
    print(f"\nUtilization:")
    print(f"{util_rate:.2f}%")

    # 3. Model Outputs Verification
    model_paths = {
        "cost": root_dir / "data" / "model_outputs" / "cost_anomaly" / "cost_anomaly_scores.parquet",
        "duplicates": root_dir / "data" / "model_outputs" / "duplicate_work" / "duplicate_scores.parquet",
        "fund": root_dir / "data" / "model_outputs" / "fund_expenditure_anomaly" / "fund_expenditure_scores.parquet",
        "delay": root_dir / "data" / "model_outputs" / "delay_rules" / "delay_scores.parquet",
    }

    df_m1 = pd.read_parquet(model_paths["cost"])
    df_m2 = pd.read_parquet(model_paths["duplicates"])
    df_m3 = pd.read_parquet(model_paths["fund"])
    df_m4 = pd.read_parquet(model_paths["delay"])

    print("\n==================================================")
    print("MODEL 1 — COST ANOMALY")
    print("==================================================")
    print(f"Input works:\n{len(df_m1):,}")
    print(f"HIGH:\n{(df_m1['severity']=='HIGH').sum():,}")
    print(f"MEDIUM:\n{(df_m1['severity']=='MEDIUM').sum():,}")
    print(f"LOW:\n{(df_m1['severity']=='LOW').sum():,}")

    print("\n==================================================")
    print("MODEL 2 — DUPLICATE WORK DETECTION")
    print("==================================================")
    print(f"Input works:\n{tot_works:,}")
    print(f"Pairs evaluated:\n{len(df_m2):,}")
    print(f"HIGH-CONFIDENCE:\n{(df_m2['severity']=='HIGH').sum():,}")
    print(f"MEDIUM:\n{(df_m2['severity']=='REVIEW').sum():,}")
    print(f"LOW:\n{(df_m2['severity']=='LOW').sum():,}")

    print("\n==================================================")
    print("MODEL 3 — FUND & EXPENDITURE ANOMALY")
    print("==================================================")
    print(f"Input works:\n{len(df_m3):,}")
    print(f"HIGH:\n{(df_m3['severity']=='HIGH').sum():,}")
    print(f"MEDIUM:\n{(df_m3['severity']=='MEDIUM').sum():,}")
    print(f"LOW:\n{(df_m3['severity']=='LOW').sum():,}")

    print("\n==================================================")
    print("MODEL 4 — STATUTORY DELAY SLA")
    print("==================================================")
    print(f"Input works:\n{len(df_m4):,}")
    print(f"HIGH:\n{(df_m4['severity']=='HIGH').sum():,}")
    print(f"MEDIUM:\n{(df_m4['severity']=='MEDIUM').sum():,}")
    print(f"LOW:\n{(df_m4['severity']=='LOW').sum():,}")

    # 4. API & Database Verification Check
    print("\n==================================================")
    print("API & DATABASE VERIFICATION")
    print("==================================================")
    try:
        req = urllib.request.urlopen("http://localhost:8000/api/v1/health")
        health = json.loads(req.read().decode())
        api_works = health.get("total_works", 0)
        api_match = (api_works == tot_works)
        print(f"API Health Total Works: {api_works:,}")
        print(f"API == DB Match: {'YES' if api_match else 'NO'}")
    except Exception as e:
        print(f"API connection failed: {e}")
        api_match = False

    print("\n==================================================")
    print("FINAL STATUS")
    print("==================================================")
    if api_match and len(df_m1) == tot_works and len(df_m3) == tot_works and len(df_m4) == tot_works:
        print("PASS")
        return True
    else:
        print("FAIL")
        return False

if __name__ == "__main__":
    run_pipeline_verification()
