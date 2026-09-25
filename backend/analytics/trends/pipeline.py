# -*- coding: utf-8 -*-
"""
Rollup Pipeline for Trend & Aggregate Analytics
MPLADS Problem Statement: MPLADS PS 190942

Executes deterministic aggregations over all 98,825 canonical works and persists
pre-computed parquet artifacts for sub-50ms API delivery.
"""

import time
from pathlib import Path
import pandas as pd
import numpy as np

from analytics.trends.aggregator import (
    prepare_canonical_work_dataset,
    aggregate_group_quarterly,
    assign_credibility_tier,
    empirical_bayes_smoothing
)
from analytics.trends.early_warning import compile_all_early_warnings


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "model_outputs" / "trends"


def run_trend_pipeline():
    print("=" * 70, flush=True)
    print("STARTING TREND & AGGREGATE ROLLUP PIPELINE", flush=True)
    print("=" * 70, flush=True)
    start_time = time.time()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    print("Loading canonical works and model outputs...", flush=True)
    works_path = DATA_DIR / "features" / "shared" / "canonical_works.parquet"
    cost_path = DATA_DIR / "model_outputs" / "cost_anomaly" / "cost_anomaly_scores.parquet"
    dup_path = DATA_DIR / "model_outputs" / "duplicate_work" / "duplicate_scores.parquet"
    fund_path = DATA_DIR / "model_outputs" / "fund_expenditure_anomaly" / "fund_expenditure_scores.parquet"
    delay_path = DATA_DIR / "model_outputs" / "delay_rules" / "delay_scores.parquet"

    df_works = pd.read_parquet(works_path)
    df_cost = pd.read_parquet(cost_path)
    df_dup = pd.read_parquet(dup_path, columns=["work_id_1", "work_id_2", "severity", "days_diff"])
    df_fund = pd.read_parquet(fund_path)
    df_delay = pd.read_parquet(delay_path)

    print(f"Loaded {len(df_works)} canonical works.", flush=True)

    # 2. Consolidate work-level dataset
    print("Consolidating work-level indicators & de-duplicating duplicate pairs...", flush=True)
    df_consolidated = prepare_canonical_work_dataset(df_works, df_cost, df_fund, df_delay, df_dup)
    print(f"Consolidated dataset shape: {df_consolidated.shape}", flush=True)

    # 3. National Quarterly Rollup
    print("Computing National quarterly trends...", flush=True)
    nat_rows = aggregate_group_quarterly(df_consolidated)
    for r in nat_rows:
        r["grain_type"] = "NATIONAL"
        r["state"] = "NATIONAL"
        r["district"] = None
        r["mp_name"] = None
        r["house"] = None

    # Compute national prior for Empirical Bayes smoothing
    tot_works_nat = len(df_consolidated)
    tot_high_cost_nat = int(df_consolidated["is_high_cost"].sum())
    national_prior_cost = tot_high_cost_nat / tot_works_nat if tot_works_nat > 0 else 0.010
    print(f"National cost anomaly prior: {national_prior_cost:.4f} ({tot_high_cost_nat}/{tot_works_nat})", flush=True)

    # 4. State Quarterly Rollups
    print("Computing State quarterly trends...", flush=True)
    state_rows = []
    for state_name, s_df in df_consolidated.groupby("state"):
        s_res = aggregate_group_quarterly(s_df, national_prior_cost=national_prior_cost, m_shrinkage=10.0)
        for r in s_res:
            r["grain_type"] = "STATE"
            r["state"] = state_name
            r["district"] = None
            r["mp_name"] = None
            r["house"] = None
        state_rows.extend(s_res)
    print(f"Generated {len(state_rows)} state-quarter rows across {df_consolidated['state'].nunique()} states.", flush=True)

    # 5. District Quarterly Rollups
    print("Computing District quarterly trends...", flush=True)
    district_rows = []
    for (state_name, dist_name), d_df in df_consolidated.groupby(["state", "district"]):
        d_res = aggregate_group_quarterly(d_df, national_prior_cost=national_prior_cost, m_shrinkage=10.0)
        for r in d_res:
            r["grain_type"] = "DISTRICT"
            r["state"] = state_name
            r["district"] = dist_name
            r["mp_name"] = None
            r["house"] = None
        district_rows.extend(d_res)
    print(f"Generated {len(district_rows)} district-quarter rows across {len(df_consolidated.groupby(['state', 'district']))} districts.", flush=True)

    # 6. MP Annual / Tenure Rollups
    print("Computing MP longitudinal trends...", flush=True)
    mp_rows = []
    for (mp_name, house_val), m_df in df_consolidated[df_consolidated["mp_name"].notna()].groupby(["mp_name", "house"]):
        for fy_val, fy_df in m_df.groupby("fiscal_year"):
            if pd.isna(fy_val):
                continue
            n_fy = len(fy_df)
            k_c = int(fy_df["is_high_cost"].sum())
            k_d = int(fy_df["is_duplicate_work"].sum())
            k_f = int(fy_df["is_high_fund"].sum())
            k_del = int(fy_df["is_high_delay"].sum())
            k_sla = int(fy_df["is_sanction_sla_compliant"].sum())

            rate_c = float(k_c / n_fy) if n_fy >= 10 else None
            rate_d = float(k_d / n_fy) if n_fy >= 10 else None
            rate_f = float(k_f / n_fy) if n_fy >= 10 else None
            rate_del = float(k_del / n_fy) if n_fy >= 10 else None
            rate_sla = float(k_sla / n_fy) if n_fy >= 10 else None

            mp_rows.append({
                "grain_type": "MP",
                "state": fy_df["state"].iloc[0] if not fy_df.empty else "N/A",
                "district": fy_df["district"].iloc[0] if not fy_df.empty else None,
                "mp_name": mp_name,
                "house": house_val,
                "year_quarter": str(fy_val),
                "quarter_start_date": "",
                "total_sanctioned_works": n_fy,
                "total_sanctioned_amount": float(fy_df["sanction_amount"].fillna(0).sum()),
                "total_disbursed_amount": float(fy_df["amount_disbursed"].fillna(0).sum()),
                "credibility_tier": assign_credibility_tier(n_fy, grain="fiscal_year"),
                "high_cost_works_count": k_c,
                "cost_anomaly_rate": rate_c,
                "cost_anomaly_rate_smoothed": empirical_bayes_smoothing(k_c, n_fy, national_prior_cost, m_weight=20.0),
                "excess_sanctioned_amount_inr": float(fy_df[fy_df["is_high_cost"]]["excess_sanction_amount"].sum()),
                "cost_trajectory": "STABLE",
                "unique_duplicate_works_count": k_d,
                "duplicate_work_rate": rate_d,
                "duplicate_cluster_density": float(fy_df["dup_pair_count"].sum() / k_d) if k_d > 0 else 0.0,
                "duplicate_exposure_inr": float(fy_df[fy_df["is_duplicate_work"]]["sanction_amount"].fillna(0).sum()),
                "high_fund_works_count": k_f,
                "fund_anomaly_rate": rate_f,
                "status_mismatch_count": int(fy_df["is_status_mismatch"].sum()),
                "dormant_sanction_count": int(fy_df["is_dormant_sanction"].sum()),
                "fund_trajectory": "STABLE",
                "sanction_sla_compliant_count": k_sla,
                "sanction_sla_compliance_rate": rate_sla,
                "mean_rec_to_sanc_delay_days": float(fy_df["rec_to_sanc_delay_days"].mean()) if n_fy > 0 else 0.0,
                "high_delay_works_count": k_del,
                "delay_rate": rate_del,
                "delay_trajectory": "STABLE",
            })
    print(f"Generated {len(mp_rows)} MP-period rows across {df_consolidated['mp_name'].nunique()} MPs.", flush=True)

    # 7. Combine rollups into master DataFrame and persist
    all_rollups = nat_rows + state_rows + district_rows + mp_rows
    df_rollups = pd.DataFrame(all_rollups)
    rollups_file = OUTPUT_DIR / "trend_quarterly_rollups.parquet"
    df_rollups.to_parquet(rollups_file, index=False)
    print(f"SUCCESS: Saved {len(df_rollups)} rollup rows to {rollups_file}", flush=True)

    # 8. Early Warnings Compilation
    print("Compiling live early warnings across statutory & statistical paradigms...", flush=True)
    all_warnings = compile_all_early_warnings(df_consolidated, df_dup)
    df_warnings = pd.DataFrame(all_warnings)
    warnings_file = OUTPUT_DIR / "early_warnings_active.parquet"
    df_warnings.to_parquet(warnings_file, index=False)
    print(f"SUCCESS: Saved {len(df_warnings)} early warnings to {warnings_file}", flush=True)

    elapsed = time.time() - start_time
    print("=" * 70, flush=True)
    print(f"TREND ROLLUP PIPELINE COMPLETE IN {elapsed:.2f} SECONDS", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    run_trend_pipeline()
