import logging
import pandas as pd
import numpy as np
from typing import Dict

from .config import VENDOR_HHI_ALERT_THRESHOLD

def compute_vendor_agency_risk_features(df_exp: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Computes procurement concentration indicators for the Vendor-Agency Risk Analyzer.
    Outputs:
      1. ida_vendor_pair_features: (IDA, Vendor) pair feature table
      2. vendor_national_features: Vendor national feature table
      3. ida_hhi_summary: Herfindahl-Hirschman Index summary by IDA
    """
    logging.info("Computing Vendor-Agency Risk Analyzer procurement concentration indicators...")
    
    exp = df_exp.copy()
    exp_valid = exp[exp["vendor_name"].notna() & exp["ida"].notna()].copy()
    exp_valid["amount"] = exp_valid["fund_disbursed_amount"].fillna(0.0)
    exp_valid["vendor_clean"] = exp_valid["vendor_name"].astype(str).str.strip()
    exp_valid["ida_clean"] = exp_valid["ida"].astype(str).str.strip()
    exp_valid["district_clean"] = exp_valid["district"].astype(str).str.strip()
    
    # 1. Total disbursement by IDA
    ida_totals = exp_valid.groupby("ida_clean")["amount"].sum().reset_index().rename(columns={"amount": "ida_total_disbursed"})
    
    # 2. Aggregations by (IDA, Vendor) pair
    pair_agg = exp_valid.groupby(["ida_clean", "district_clean", "vendor_clean"]).agg(
        vendor_ida_transaction_count=("amount", "count"),
        vendor_ida_total_disbursed=("amount", "sum"),
        distinct_works_count=("work_id", "nunique"),
        distinct_mps_count=("mp_name", "nunique")
    ).reset_index().rename(columns={"ida_clean": "ida", "district_clean": "district", "vendor_clean": "vendor_name"})
    
    # Merge IDA total disbursement
    pair_agg = pd.merge(pair_agg, ida_totals.rename(columns={"ida_clean": "ida"}), on="ida", how="left")
    
    # Calculate Vendor Share in IDA
    tot = pair_agg["ida_total_disbursed"]
    pair_agg["vendor_share_in_ida"] = np.where(tot > 0, pair_agg["vendor_ida_total_disbursed"] / tot, 0.0)
    pair_agg["is_dominant_vendor_flag"] = pair_agg["vendor_share_in_ida"] > 0.50
    
    # 3. Calculate Herfindahl-Hirschman Index (HHI) per IDA
    # HHI = sum((vendor_share)^2) for all vendors in that IDA
    hhi_list = []
    for ida_val, group in pair_agg.groupby("ida"):
        hhi_val = float(np.sum(group["vendor_share_in_ida"] ** 2))
        vendor_cnt = len(group)
        hhi_list.append({
            "ida": ida_val,
            "district": group["district"].iloc[0],
            "ida_total_disbursed": group["ida_total_disbursed"].iloc[0],
            "vendor_count_in_ida": vendor_cnt,
            "ida_vendor_hhi": hhi_val,
            "is_high_procurement_risk_ida": hhi_val > VENDOR_HHI_ALERT_THRESHOLD # Configurable risk indicator threshold
        })
    df_hhi = pd.DataFrame(hhi_list)
    
    # Merge IDA HHI back into pair features
    pair_agg = pd.merge(pair_agg, df_hhi[["ida", "ida_vendor_hhi", "is_high_procurement_risk_ida"]], on="ida", how="left")
    
    # 4. Vendor National Level Aggregation
    vendor_nat = exp_valid.groupby("vendor_clean").agg(
        vendor_total_disbursed_national=("amount", "sum"),
        vendor_total_transactions_national=("amount", "count"),
        vendor_distinct_ida_count=("ida_clean", "nunique"),
        vendor_distinct_mp_count=("mp_name", "nunique"),
        vendor_distinct_works_count=("work_id", "nunique")
    ).reset_index().rename(columns={"vendor_clean": "vendor_name"})
    
    vendor_nat["vendor_multi_district_flag"] = vendor_nat["vendor_distinct_ida_count"] > 1
    
    logging.info(f"Vendor-Agency Risk features computed: {len(pair_agg):,} (IDA, Vendor) pairs across {len(df_hhi):,} IDAs and {len(vendor_nat):,} distinct vendors.")
    
    return {
        "ida_vendor_pair_features": pair_agg,
        "vendor_national_features": vendor_nat,
        "ida_hhi_summary": df_hhi
    }
