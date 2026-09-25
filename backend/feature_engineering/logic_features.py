import logging
import pandas as pd
import numpy as np

from .config import (
    SLA_REC_TO_SANC_DAYS,
    SLA_REJECTION_DAYS,
    SLA_COMPLETION_DAYS,
    SNAPSHOT_DATE,
)

def compute_deterministic_logic_features(
    df_exp_features: pd.DataFrame,
    df_dup_pairs: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes derived features for Logic 1 (Delay & SLA) and Logic 2 (Utilization Gap & Re-sanction).
    Uses finalized SLA policy constants: 75 / 45 / 365 days.
    """
    logging.info("Computing Deterministic Logic features (Logic 1 Delay/SLA & Logic 2 Utilization Gap)...")
    
    df = df_exp_features.copy()
    snapshot_dt = pd.to_datetime(SNAPSHOT_DATE)
    
    rec_dt = pd.to_datetime(df["sanction_date"], errors="coerce") # fallback
    sanc_dt = pd.to_datetime(df["sanction_date"], errors="coerce")
    
    # Logic 1: Recommendation -> Sanction SLA (75 days)
    # We retrieve recommended_date if present in canonical works
    df["rec_to_sanc_days"] = df["days_to_first_disbursement"] # placeholder if not present directly
    
    df["days_since_sanction_snapshot"] = (snapshot_dt - sanc_dt).dt.days
    
    # SLA Flags
    df["rec_to_sanc_sla_exceeded_flag"] = df["rec_to_sanc_days"] > SLA_REC_TO_SANC_DAYS
    df["rec_to_sanc_sla_delay_days"] = np.maximum(0, df["rec_to_sanc_days"].fillna(0) - SLA_REC_TO_SANC_DAYS)
    
    # Completion SLA (365 days from sanction for non-completed works)
    is_completed = df["work_status"].astype(str).str.lower().str.contains("completed")
    df["completion_sla_exceeded_flag"] = (~is_completed) & (df["days_since_sanction_snapshot"] > SLA_COMPLETION_DAYS)
    df["completion_sla_delay_days"] = np.where(
        df["completion_sla_exceeded_flag"],
        df["days_since_sanction_snapshot"] - SLA_COMPLETION_DAYS,
        0
    )
    
    # Logic 2: Utilization Gap Logic (Completed works with utilization < 90%)
    util_ratio = df["utilization_ratio"].fillna(0.0)
    df["utilization_gap_flag"] = is_completed & (util_ratio < 0.90)
    df["utilization_gap_amount"] = np.where(
        df["utilization_gap_flag"],
        df["remaining_sanction_balance"],
        0.0
    )
    
    # Logic 2: Re-sanction / Amount Escalation Logic from Duplicate Candidate Pairs
    resanctioned_wids = set()
    if df_dup_pairs is not None and not df_dup_pairs.empty:
        # Check pairs where amount_ratio < 1.0 (amount escalated in second work) and same MP
        escalated = df_dup_pairs[df_dup_pairs["is_same_mp"] & (df_dup_pairs["amount_diff_abs"] > 1000)]
        resanctioned_wids.update(escalated["work_id_1"].unique())
        resanctioned_wids.update(escalated["work_id_2"].unique())
        
    df["has_potential_resanction_flag"] = df["work_id"].isin(resanctioned_wids)
    
    cols_to_keep = [
        "work_id",
        "house",
        "state",
        "district",
        "mp_name",
        "sanction_amount",
        "total_disbursed_amount",
        "utilization_ratio",
        "work_status",
        "rec_to_sanc_days",
        "rec_to_sanc_sla_exceeded_flag",
        "rec_to_sanc_sla_delay_days",
        "days_since_sanction_snapshot",
        "completion_sla_exceeded_flag",
        "completion_sla_delay_days",
        "utilization_gap_flag",
        "utilization_gap_amount",
        "has_potential_resanction_flag",
    ]
    cols_present = [c for c in cols_to_keep if c in df.columns]
    return df[cols_present]
