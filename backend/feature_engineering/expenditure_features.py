import logging
import pandas as pd
import numpy as np

def compute_expenditure_model_features(
    df_works: pd.DataFrame,
    df_exp: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes work-level financial features for Model 3 (Expenditure Anomaly Detector).
    Aggregates transaction-level expenditure rows using vectorized Pandas operations.
    """
    logging.info("Computing Model 3 Expenditure & Fund Utilization features...")
    
    works = df_works.copy()
    exp = df_exp.copy()
    
    # Filter valid expenditures with work_id
    exp_valid = exp[exp["work_id"].notna()].copy()
    exp_valid["amount"] = exp_valid["fund_disbursed_amount"].fillna(0.0)
    exp_valid["exp_dt"] = pd.to_datetime(exp_valid["expenditure_date"], errors="coerce")
    exp_valid["status_clean"] = exp_valid["payment_status"].astype(str).str.lower()
    exp_valid["is_success"] = exp_valid["status_clean"].str.contains("success").astype(int)
    exp_valid["is_progress"] = exp_valid["status_clean"].str.contains("progress").astype(int)
    
    # Primary Vectorized Aggregation by work_id
    exp_agg = exp_valid.groupby("work_id").agg(
        total_disbursed_amount=("amount", "sum"),
        transaction_count=("amount", "count"),
        max_single_payment=("amount", "max"),
        mean_single_payment=("amount", "mean"),
        vendor_count=("vendor_name", "nunique"),
        first_expenditure_date=("exp_dt", "min"),
        last_expenditure_date=("exp_dt", "max"),
        payment_success_count=("is_success", "sum"),
        payment_inprogress_count=("is_progress", "sum")
    ).reset_index()
    
    exp_agg["max_payment_ratio"] = np.where(
        exp_agg["total_disbursed_amount"] > 0,
        exp_agg["max_single_payment"] / exp_agg["total_disbursed_amount"],
        0.0
    )
    exp_agg["is_payment_ongoing_flag"] = exp_agg["payment_inprogress_count"] > 0
    
    # Calculate spending window days and velocity
    first_dt = pd.to_datetime(exp_agg["first_expenditure_date"], errors="coerce")
    last_dt = pd.to_datetime(exp_agg["last_expenditure_date"], errors="coerce")
    window_days = (last_dt - first_dt).dt.days.fillna(0).astype(int)
    exp_agg["spending_window_days"] = window_days
    
    tot_amt = exp_agg["total_disbursed_amount"]
    exp_agg["spending_velocity_per_day"] = np.where(
        window_days > 0,
        tot_amt / np.maximum(1, window_days),
        tot_amt
    )
    
    # Calculate Herfindahl Index (HHI) across payee vendors per work_id (SRS § 5.3)
    exp_valid["vendor_clean"] = exp_valid["vendor_name"].fillna("UNKNOWN_VENDOR").astype(str).str.strip()
    vendor_exp = exp_valid.groupby(["work_id", "vendor_clean"])["amount"].sum().reset_index()
    work_vendor_tot = vendor_exp.groupby("work_id")["amount"].transform("sum")
    vendor_exp["vendor_share"] = np.where(work_vendor_tot > 0, vendor_exp["amount"] / work_vendor_tot, 0.0)
    vendor_exp["vendor_share_sq"] = vendor_exp["vendor_share"] ** 2
    vendor_hhi_df = vendor_exp.groupby("work_id")["vendor_share_sq"].sum().reset_index().rename(
        columns={"vendor_share_sq": "payment_concentration_hhi"}
    )
    
    # Also calculate tranche-level HHI for auditing reference
    work_tot = exp_valid.groupby("work_id")["amount"].transform("sum")
    exp_valid["tranche_share"] = np.where(work_tot > 0, exp_valid["amount"] / work_tot, 0.0)
    exp_valid["tranche_share_sq"] = exp_valid["tranche_share"] ** 2
    tranche_hhi_df = exp_valid.groupby("work_id")["tranche_share_sq"].sum().reset_index().rename(
        columns={"tranche_share_sq": "tranche_concentration_hhi"}
    )
    
    exp_agg = pd.merge(exp_agg, vendor_hhi_df, on="work_id", how="left")
    exp_agg = pd.merge(exp_agg, tranche_hhi_df, on="work_id", how="left")
    
    # Format date strings
    exp_agg["first_expenditure_date"] = first_dt.dt.strftime("%Y-%m-%d")
    exp_agg["last_expenditure_date"] = last_dt.dt.strftime("%Y-%m-%d")
    
    # Merge with works master table
    works_cols = [c for c in ["work_id", "house", "state", "district", "ida", "mp_name", "constituency_or_term", "work_category", "work_type_template", "sanction_amount", "sanction_date", "work_status"] if c in works.columns]
    df_out = pd.merge(works[works_cols], exp_agg, on="work_id", how="left")
    
    # Fill zero expenditures for sanctioned works that have no expenditure transactions yet
    df_out["total_disbursed_amount"] = df_out["total_disbursed_amount"].fillna(0.0)
    df_out["transaction_count"] = df_out["transaction_count"].fillna(0).astype(int)
    df_out["vendor_count"] = df_out["vendor_count"].fillna(0).astype(int)
    df_out["payment_concentration_hhi"] = df_out["payment_concentration_hhi"].fillna(0.0)
    df_out["tranche_concentration_hhi"] = df_out["tranche_concentration_hhi"].fillna(0.0)
    
    sanc_amt = df_out["sanction_amount"].fillna(0.0)
    disb_amt = df_out["total_disbursed_amount"]
    
    # Compute utilization ratio capped at 1.00 (per Phase 1 Spec §0.4)
    raw_util = np.where(sanc_amt > 0, disb_amt / sanc_amt, 0.0)
    df_out["utilization_ratio"] = np.minimum(1.00, raw_util)
    df_out["remaining_sanction_balance"] = np.maximum(0.0, sanc_amt - disb_amt)
    
    # Days from sanction to first expenditure
    sanc_dt = pd.to_datetime(df_out["sanction_date"], errors="coerce")
    first_exp_dt = pd.to_datetime(df_out["first_expenditure_date"], errors="coerce")
    df_out["days_to_first_disbursement"] = (first_exp_dt - sanc_dt).dt.days
    
    logging.info(f"Model 3 expenditure features computed for {len(df_out):,} works. Total aggregated expenditure: ₹{df_out['total_disbursed_amount'].sum():,.2f}")
    return df_out
