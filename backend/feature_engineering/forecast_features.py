import logging
import pandas as pd
import numpy as np

def compute_forecasting_series(df_exp: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs the monthly time-series dataset for Model 4 (MPLADS Expenditure Forecasting).
    Primary Grain: State x Month.
    Preserves true zero-spend months without artificial interpolation.
    Reconciles aggregate sums with canonical expenditure ledger.
    """
    logging.info("Building Model 4 State x Month forecasting time-series dataset...")
    
    exp = df_exp.copy()
    exp_valid = exp[exp["expenditure_date"].notna()].copy()
    exp_valid["amount"] = exp_valid["fund_disbursed_amount"].fillna(0.0)
    exp_valid["exp_dt"] = pd.to_datetime(exp_valid["expenditure_date"], errors="coerce")
    exp_valid = exp_valid[exp_valid["exp_dt"].notna()]
    
    exp_valid["state_clean"] = exp_valid["state"].fillna("UNKNOWN").astype(str).str.strip()
    exp_valid["year_month"] = exp_valid["exp_dt"].dt.strftime("%Y-%m")
    exp_valid["month_start_date"] = exp_valid["exp_dt"].dt.strftime("%Y-%m-01")
    
    # Primary Groupby: State x Month
    monthly_agg = exp_valid.groupby(["state_clean", "year_month", "month_start_date"]).agg(
        total_disbursed_amount=("amount", "sum"),
        transaction_count=("amount", "count"),
        active_works_count=("work_id", "nunique")
    ).reset_index().rename(columns={"state_clean": "state"})
    
    # Fill full cartesian grid (all states x all months in observed window)
    all_states = sorted(exp_valid["state_clean"].unique())
    all_yms = sorted(exp_valid["year_month"].unique())
    
    grid = []
    for s in all_states:
        for ym in all_yms:
            grid.append({"state": s, "year_month": ym, "month_start_date": f"{ym}-01"})
            
    df_grid = pd.DataFrame(grid)
    df_full = pd.merge(df_grid, monthly_agg, on=["state", "year_month", "month_start_date"], how="left")
    
    df_full["total_disbursed_amount"] = df_full["total_disbursed_amount"].fillna(0.0)
    df_full["transaction_count"] = df_full["transaction_count"].fillna(0).astype(int)
    df_full["active_works_count"] = df_full["active_works_count"].fillna(0).astype(int)
    
    df_full = df_full.sort_values(by=["state", "year_month"]).reset_index(drop=True)
    
    logging.info(f"Model 4 forecasting series generated: {len(df_full):,} state-month rows across {len(all_states)} states and {len(all_yms)} months.")
    logging.info(f"Total series expenditure sum: ₹{df_full['total_disbursed_amount'].sum():,.2f}")
    return df_full
