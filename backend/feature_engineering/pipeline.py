import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from .config import (
    FEATURES_DIR,
    REPORTS_DIR,
    SHARED_FEATURES_DIR,
    COST_FEATURES_DIR,
    EXPENDITURE_FEATURES_DIR,
    DUPLICATE_FEATURES_DIR,
    FORECAST_FEATURES_DIR,
    LOGIC_FEATURES_DIR,
    COMPLIANCE_FEATURES_DIR,
    VENDOR_FEATURES_DIR,
)
from .canonical import build_canonical_layer
from .work_features import compute_cost_model_features
from .duplicate_candidates import generate_duplicate_candidate_pairs
from .expenditure_features import compute_expenditure_model_features
from .forecast_features import compute_forecasting_series
from .logic_features import compute_deterministic_logic_features
from .compliance_features import compute_compliance_features
from .vendor_features import compute_vendor_agency_risk_features
from .validators import validate_feature_reconciliation, assert_model1_leakage_free
from .feature_registry import generate_feature_quality_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_feature_pipeline() -> Dict[str, pd.DataFrame]:
    """
    Orchestrates the Phase 3 Canonical Data & Feature Engineering Pipeline.
    """
    logging.info("Starting Phase 3 Feature Engineering Pipeline...")
    
    # Create required output directories
    for d in [
        FEATURES_DIR, REPORTS_DIR, SHARED_FEATURES_DIR, COST_FEATURES_DIR,
        EXPENDITURE_FEATURES_DIR, DUPLICATE_FEATURES_DIR, FORECAST_FEATURES_DIR,
        LOGIC_FEATURES_DIR, COMPLIANCE_FEATURES_DIR, VENDOR_FEATURES_DIR
    ]:
        d.mkdir(parents=True, exist_ok=True)
        
    # 1. Build Canonical Layer
    canonical = build_canonical_layer()
    df_works = canonical["canonical_works"]
    df_exp = canonical["canonical_expenditures"]
    df_mp_alloc = canonical["canonical_mp_allocations"]
    df_calamity = canonical["canonical_calamity"]
    
    # 2. Compute Model 1 Cost Anomaly Features (Sanction-time only)
    df_cost = compute_cost_model_features(df_works)
    assert_model1_leakage_free(df_cost)
    
    # 3. Compute Model 2 Duplicate Candidate Pairs
    df_dup = generate_duplicate_candidate_pairs(df_works)
    
    # 4. Compute Model 3 Expenditure Anomaly Features
    df_exp_feat = compute_expenditure_model_features(df_works, df_exp)
    
    # 5. Compute Model 4 Forecasting Series
    df_forecast = compute_forecasting_series(df_exp)
    
    # 6. Compute Logic 1 & Logic 2 Deterministic Features
    df_logic = compute_deterministic_logic_features(df_exp_feat, df_dup)
    
    # 7. Compute Logic 3 Compliance Features
    df_compliance = compute_compliance_features(df_works, df_mp_alloc, df_calamity, df_exp)
    
    # 8. Compute Vendor-Agency Risk Analyzer Features
    vendor_dict = compute_vendor_agency_risk_features(df_exp)
    df_ida_vendor = vendor_dict["ida_vendor_pair_features"]
    df_vendor_nat = vendor_dict["vendor_national_features"]
    df_ida_hhi = vendor_dict["ida_hhi_summary"]
    
    # 9. Perform Integrity Reconciliation Validation
    recon_results = validate_feature_reconciliation(df_exp, df_exp_feat, df_forecast)
    logging.info(f"Reconciliation Results: {recon_results}")
    
    # 10. Save Parquet Output Datasets
    df_works.to_parquet(SHARED_FEATURES_DIR / "canonical_works.parquet", index=False)
    df_cost.to_parquet(COST_FEATURES_DIR / "cost_anomaly_features.parquet", index=False)
    df_dup.to_parquet(DUPLICATE_FEATURES_DIR / "duplicate_candidate_pairs.parquet", index=False)
    df_exp_feat.to_parquet(EXPENDITURE_FEATURES_DIR / "expenditure_anomaly_features.parquet", index=False)
    df_forecast.to_parquet(FORECAST_FEATURES_DIR / "monthly_forecasting_series.parquet", index=False)
    df_logic.to_parquet(LOGIC_FEATURES_DIR / "deterministic_logic_features.parquet", index=False)
    df_compliance.to_parquet(COMPLIANCE_FEATURES_DIR / "compliance_rule_features.parquet", index=False)
    df_ida_vendor.to_parquet(VENDOR_FEATURES_DIR / "ida_vendor_pair_features.parquet", index=False)
    df_vendor_nat.to_parquet(VENDOR_FEATURES_DIR / "vendor_national_features.parquet", index=False)
    df_ida_hhi.to_parquet(VENDOR_FEATURES_DIR / "ida_hhi_summary.parquet", index=False)
    
    # 11. Export Feature Registry and Quality Diagnostics Report
    feature_tables = {
        "cost_anomaly_features": df_cost,
        "duplicate_candidate_pairs": df_dup,
        "expenditure_anomaly_features": df_exp_feat,
        "monthly_forecasting_series": df_forecast,
        "deterministic_logic_features": df_logic,
        "compliance_rule_features": df_compliance,
        "ida_vendor_pair_features": df_ida_vendor,
        "vendor_national_features": df_vendor_nat,
        "ida_hhi_summary": df_ida_hhi
    }
    
    report_json = REPORTS_DIR / "feature_quality_report.json"
    report_md = REPORTS_DIR / "feature_quality_report.md"
    generate_feature_quality_report(feature_tables, report_json, report_md)
    
    # Also save standalone feature_registry.json
    with open(REPORTS_DIR / "feature_registry.json", "w", encoding="utf-8") as f:
        import json
        from .feature_registry import FEATURE_REGISTRY_ENTRIES, REJECTED_FEATURE_ENTRIES
        json.dump({
            "status": "PHASE 3 COMPLETE",
            "feature_registry": FEATURE_REGISTRY_ENTRIES,
            "rejected_features": REJECTED_FEATURE_ENTRIES
        }, f, indent=2)
        
    logging.info("Phase 3 Pipeline completed successfully!")
    
    return {
        "canonical_works": df_works,
        "cost_features": df_cost,
        "duplicate_pairs": df_dup,
        "expenditure_features": df_exp_feat,
        "forecast_series": df_forecast,
        "logic_features": df_logic,
        "compliance_features": df_compliance,
        "ida_vendor_pair": df_ida_vendor,
        "vendor_national": df_vendor_nat,
        "ida_hhi": df_ida_hhi
    }

if __name__ == "__main__":
    run_feature_pipeline()
