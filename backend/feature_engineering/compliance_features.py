import logging
import pandas as pd
import numpy as np

def compute_compliance_features(
    df_works: pd.DataFrame,
    df_mp_alloc: pd.DataFrame,
    df_calamity: pd.DataFrame,
    df_exp: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes compliance rule metrics for Logic 3 (Compliance Rule Engine).
    Aggregates cumulative MP sanctions vs allocated limit, and calamity consent vs spending.
    """
    logging.info("Computing Logic 3 Compliance Rule features...")
    
    mp_alloc = df_mp_alloc.copy()
    works = df_works.copy()
    
    # 1. MP Entitlement Ceiling Compliance
    # Calculate cumulative sanctioned amount per MP
    works["sanc_amt"] = works["sanction_amount"].fillna(0.0)
    mp_sanc = works.groupby("mp_name")["sanc_amt"].agg(
        cumulative_sanctioned_amount="sum",
        sanctioned_works_count="count"
    ).reset_index()
    
    mp_alloc["alloc_amt"] = mp_alloc["allocated_amount"].fillna(0.0)
    mp_alloc_clean = mp_alloc.groupby("mp_name").agg(
        house=("house", "first"),
        state=("state", "first"),
        constituency_or_term=("constituency_or_term", "first"),
        allocated_amount=("alloc_amt", "max")
    ).reset_index()
    
    df_comp = pd.merge(mp_alloc_clean, mp_sanc, on="mp_name", how="left")
    df_comp["cumulative_sanctioned_amount"] = df_comp["cumulative_sanctioned_amount"].fillna(0.0)
    df_comp["sanctioned_works_count"] = df_comp["sanctioned_works_count"].fillna(0).astype(int)
    
    alloc = df_comp["allocated_amount"]
    cum_sanc = df_comp["cumulative_sanctioned_amount"]
    
    df_comp["entitlement_utilization_pct"] = np.where(alloc > 0, (cum_sanc / alloc) * 100.0, 0.0)
    df_comp["entitlement_exceeded_flag"] = cum_sanc > alloc
    df_comp["entitlement_excess_amount"] = np.maximum(0.0, cum_sanc - alloc)
    
    # 2. Calamity Consent Compliance
    if df_calamity is not None and not df_calamity.empty:
        cal = df_calamity.copy()
        cal["cons_amt"] = cal["consent_amount"].fillna(0.0)
        cal_agg = cal.groupby("mp_name")["cons_amt"].sum().reset_index().rename(columns={"cons_amt": "calamity_consent_amount"})
        df_comp = pd.merge(df_comp, cal_agg, on="mp_name", how="left")
        df_comp["calamity_consent_amount"] = df_comp["calamity_consent_amount"].fillna(0.0)
    else:
        df_comp["calamity_consent_amount"] = 0.0
        
    logging.info(f"Logic 3 compliance features computed for {len(df_comp):,} MPs. Entitlement exceeded count: {df_comp['entitlement_exceeded_flag'].sum()}")
    return df_comp
