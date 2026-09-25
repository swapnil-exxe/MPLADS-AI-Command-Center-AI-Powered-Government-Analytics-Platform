import numpy as np
import pandas as pd
from typing import Tuple

from .config import PEER_MIN_GROUP_SIZE

def compute_work_shared_features(df_works: pd.DataFrame) -> pd.DataFrame:
    """
    Computes shared work-level features from canonical_works.
    Unit of analysis: work (1 row per work_id).
    """
    df = df_works.copy()
    
    # Recommended -> Sanction duration (days)
    rec_dt = pd.to_datetime(df["recommended_date"], errors="coerce")
    sanc_dt = pd.to_datetime(df["sanction_date"], errors="coerce")
    df["rec_to_sanc_days"] = (sanc_dt - rec_dt).dt.days
    
    # Description character length and word count
    desc_str = df["work_description"].fillna("").astype(str)
    df["desc_char_len"] = desc_str.apply(len)
    df["desc_word_count"] = desc_str.apply(lambda s: len(s.split()))
    
    # Log transforms of monetary amounts
    sanc_amt = df["sanction_amount"].fillna(0.0)
    df["sanction_amount_log"] = np.log1p(np.maximum(0.0, sanc_amt))
    
    # Data quality exception flag (< 1,000 INR sanction floor)
    df["is_data_quality_exception"] = (sanc_amt < 1000.0) & (sanc_amt > 0.0)
    
    return df

def compute_cost_model_features(df_works: pd.DataFrame) -> pd.DataFrame:
    """
    Computes features specifically for Model 1 (Anomalous Cost Estimate Detector).
    STRICT LEAKAGE CONTROL: Uses ONLY sanction-time features. NO expenditure or post-sanction fields!
    
    Implements Hierarchical Fallback Peer Grouping:
      1. State x work_type_template (Fine)
      2. work_type_template (Coarse / National)
      3. National overall
    """
    df = compute_work_shared_features(df_works)
    
    # Clean template strings
    df["work_type_clean"] = df["work_type_template"].fillna("UNCLASSIFIED").astype(str).str.strip()
    df["state_clean"] = df["state"].fillna("UNKNOWN").astype(str).str.strip()
    
    # Peer group keys
    df["peer_group_fine"] = df["state_clean"] + " || " + df["work_type_clean"]
    df["peer_group_coarse"] = df["work_type_clean"]
    
    # Calculate stats for fine peer groups (State x Work Type)
    fine_stats = df.groupby("peer_group_fine")["sanction_amount"].agg(
        fine_count="count",
        fine_median="median",
        fine_q25=lambda s: s.quantile(0.25),
        fine_q75=lambda s: s.quantile(0.75)
    ).reset_index()
    fine_stats["fine_iqr"] = fine_stats["fine_q75"] - fine_stats["fine_q25"]
    
    # Calculate stats for coarse peer groups (Work Type National)
    coarse_stats = df.groupby("peer_group_coarse")["sanction_amount"].agg(
        coarse_count="count",
        coarse_median="median",
        coarse_q25=lambda s: s.quantile(0.25),
        coarse_q75=lambda s: s.quantile(0.75)
    ).reset_index()
    coarse_stats["coarse_iqr"] = coarse_stats["coarse_q75"] - coarse_stats["coarse_q25"]
    
    # National stats fallback
    nat_median = float(df["sanction_amount"].median())
    nat_q25 = float(df["sanction_amount"].quantile(0.25))
    nat_q75 = float(df["sanction_amount"].quantile(0.75))
    nat_iqr = max(1.0, nat_q75 - nat_q25)
    
    # Merge peer group stats back
    df = pd.merge(df, fine_stats, on="peer_group_fine", how="left")
    df = pd.merge(df, coarse_stats, on="peer_group_coarse", how="left")
    
    # Apply hierarchical fallback logic
    peer_level = []
    peer_count = []
    peer_median = []
    peer_iqr = []
    
    for idx, row in df.iterrows():
        f_cnt = row["fine_count"]
        c_cnt = row["coarse_count"]
        
        if pd.notna(f_cnt) and f_cnt >= PEER_MIN_GROUP_SIZE:
            peer_level.append("STATE")
            peer_count.append(int(f_cnt))
            peer_median.append(float(row["fine_median"]))
            peer_iqr.append(float(max(1.0, row["fine_iqr"])))
        elif pd.notna(c_cnt) and c_cnt >= PEER_MIN_GROUP_SIZE:
            peer_level.append("NATIONAL_TYPE")
            peer_count.append(int(c_cnt))
            peer_median.append(float(row["coarse_median"]))
            peer_iqr.append(float(max(1.0, row["coarse_iqr"])))
        else:
            peer_level.append("NATIONAL_ALL")
            peer_count.append(len(df))
            peer_median.append(nat_median)
            peer_iqr.append(nat_iqr)
            
    df["peer_level_used"] = peer_level
    df["peer_group_size"] = peer_count
    df["peer_median_amount"] = peer_median
    df["peer_iqr_amount"] = peer_iqr
    
    # Calculate robust IQR deviation and cost ratio vs peer median
    # IQR / 1.349 translates IQR to Gaussian standard deviation scale
    sanc_amt = df["sanction_amount"].fillna(0.0)
    iqr_denom = np.maximum(100.0, df["peer_iqr_amount"] / 1.349)
    df["peer_iqr_deviation"] = (sanc_amt - df["peer_median_amount"]) / iqr_denom
    df["cost_ratio_vs_peer_median"] = sanc_amt / np.maximum(100.0, df["peer_median_amount"])
    
    # Filter to final Model 1 feature columns
    cols_to_keep = [
        "work_id",
        "house",
        "state",
        "district",
        "ida",
        "mp_name",
        "constituency_or_term",
        "work_category",
        "work_type_template",
        "work_description",
        "sanction_amount",
        "sanction_amount_log",
        "rec_to_sanc_days",
        "desc_char_len",
        "desc_word_count",
        "is_data_quality_exception",
        "peer_level_used",
        "peer_group_size",
        "peer_median_amount",
        "peer_iqr_amount",
        "peer_iqr_deviation",
        "cost_ratio_vs_peer_median",
    ]
    cols_present = [c for c in cols_to_keep if c in df.columns]
    return df[cols_present]
