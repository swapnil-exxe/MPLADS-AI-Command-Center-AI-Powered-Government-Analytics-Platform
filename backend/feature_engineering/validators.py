import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

def validate_feature_reconciliation(
    df_exp_source: pd.DataFrame,
    df_exp_features: pd.DataFrame,
    df_forecast_series: pd.DataFrame
) -> Dict[str, Any]:
    """
    Performs mathematical reconciliation checks across canonical data and feature datasets.
    """
    logging.info("Validating feature reconciliation & integrity constraints...")
    
    source_total_exp = float(df_exp_source["fund_disbursed_amount"].fillna(0.0).sum())
    agg_total_exp = float(df_exp_features["total_disbursed_amount"].sum())
    forecast_total_exp = float(df_forecast_series["total_disbursed_amount"].sum())
    
    exp_diff = abs(source_total_exp - agg_total_exp)
    forecast_diff = abs(source_total_exp - forecast_total_exp)
    
    exp_reconciled = exp_diff < 1.0 # Within 1 INR rounding
    forecast_reconciled = forecast_diff < 1.0
    
    results = {
        "source_total_expenditure": source_total_exp,
        "work_aggregated_expenditure": agg_total_exp,
        "expenditure_reconciled": exp_reconciled,
        "expenditure_diff_inr": exp_diff,
        "monthly_forecast_expenditure": forecast_total_exp,
        "forecast_reconciled": forecast_reconciled,
        "forecast_diff_inr": forecast_diff,
    }
    
    if not exp_reconciled:
        logging.warning(f"Expenditure reconciliation mismatch! Source: ₹{source_total_exp:,.2f}, Aggregated: ₹{agg_total_exp:,.2f}")
    else:
        logging.info(f"Expenditure reconciliation PASSED: ₹{source_total_exp:,.2f}")
        
    if not forecast_reconciled:
        logging.warning(f"Forecast reconciliation mismatch! Source: ₹{source_total_exp:,.2f}, Forecast: ₹{forecast_total_exp:,.2f}")
    else:
        logging.info(f"Forecast reconciliation PASSED: ₹{source_total_exp:,.2f}")
        
    return results

def assert_model1_leakage_free(df_cost_features: pd.DataFrame):
    """
    Asserts that Model 1 cost feature table contains NO post-sanction fields.
    """
    forbidden = ["expenditure_date", "completion_date", "payment_status", "fund_disbursed_amount", "utilization_ratio", "total_disbursed_amount"]
    leaked = [c for c in forbidden if c in df_cost_features.columns]
    if leaked:
        raise ValueError(f"LEAKAGE DETECTED in Model 1 features: {leaked}")
    logging.info("Model 1 Zero-Leakage check PASSED. No post-sanction columns found.")
