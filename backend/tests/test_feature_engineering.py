import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from feature_engineering.config import (
    PROCESSED_DATA_DIR,
    SLA_REC_TO_SANC_DAYS,
    SLA_REJECTION_DAYS,
    SLA_COMPLETION_DAYS,
    DUPLICATE_BLOCKING_WINDOW_DAYS,
    DUPLICATE_AMOUNT_RATIO_THRESHOLD,
    VENDOR_HHI_ALERT_THRESHOLD,
)
from feature_engineering.canonical import build_canonical_layer
from feature_engineering.work_features import compute_cost_model_features, compute_work_shared_features
from feature_engineering.duplicate_candidates import generate_duplicate_candidate_pairs
from feature_engineering.expenditure_features import compute_expenditure_model_features
from feature_engineering.forecast_features import compute_forecasting_series
from feature_engineering.logic_features import compute_deterministic_logic_features
from feature_engineering.compliance_features import compute_compliance_features
from feature_engineering.vendor_features import compute_vendor_agency_risk_features
from feature_engineering.validators import validate_feature_reconciliation, assert_model1_leakage_free

def test_canonical_layer_building():
    """Verify that canonical layer is properly loaded and normalized."""
    canonical = build_canonical_layer()
    assert "canonical_works" in canonical
    assert "canonical_expenditures" in canonical
    assert "canonical_mp_allocations" in canonical
    assert "canonical_calamity" in canonical
    
    df_works = canonical["canonical_works"]
    assert len(df_works) > 0
    assert "work_id" in df_works.columns
    assert "house" in df_works.columns
    assert "constituency_or_term" in df_works.columns
    assert df_works["work_id"].nunique() == len(df_works)

def test_model1_zero_leakage_and_peer_grouping():
    """Verify Model 1 cost features contain zero post-sanction leakage."""
    canonical = build_canonical_layer()
    df_works = canonical["canonical_works"]
    
    df_cost = compute_cost_model_features(df_works)
    
    # Assert zero leakage
    assert_model1_leakage_free(df_cost)
    
    # Check expected features
    assert "sanction_amount_log" in df_cost.columns
    assert "peer_iqr_deviation" in df_cost.columns
    assert "cost_ratio_vs_peer_median" in df_cost.columns
    assert "peer_level_used" in df_cost.columns
    
    # Verify peer_level_used contains fallback levels
    levels = df_cost["peer_level_used"].unique()
    assert len(levels) > 0

def test_model2_duplicate_blocking_window():
    """Verify candidate pair generation enforces 90-day blocking window."""
    canonical = build_canonical_layer()
    df_works = canonical["canonical_works"]
    
    df_pairs = generate_duplicate_candidate_pairs(df_works)
    if not df_pairs.empty:
        assert (df_pairs["days_diff"] <= DUPLICATE_BLOCKING_WINDOW_DAYS).all()
        assert (df_pairs["amount_ratio"] >= DUPLICATE_AMOUNT_RATIO_THRESHOLD).all()
        assert (df_pairs["work_id_1"] < df_pairs["work_id_2"]).all()

def test_duplicate_candidate_pair_uniqueness_and_canonical_ordering():
    """Verification Check 3: Verify candidate pair uniqueness, zero self-pairs, zero bidirectional duplicates, and canonical ordering."""
    canonical = build_canonical_layer()
    df_works = canonical["canonical_works"]
    
    df_pairs = generate_duplicate_candidate_pairs(df_works)
    assert not df_pairs.empty
    
    # 1. Zero self-pairs
    assert (df_pairs["work_id_1"] != df_pairs["work_id_2"]).all()
    
    # 2. Canonical ordering work_id_1 < work_id_2
    assert (df_pairs["work_id_1"] < df_pairs["work_id_2"]).all()
    
    # 3. Unique pair strings (zero bidirectional duplicates)
    pair_strings = df_pairs["work_id_1"].astype(str) + "||" + df_pairs["work_id_2"].astype(str)
    assert pair_strings.nunique() == len(df_pairs)
    
    # 4. Strict blocking condition verification
    assert (df_pairs["days_diff"] <= 90).all()
    assert (df_pairs["amount_ratio"] >= DUPLICATE_AMOUNT_RATIO_THRESHOLD).all()

def test_model3_expenditure_reconciliation():
    """Verify Model 3 expenditure aggregation matches canonical total expenditure sum."""
    canonical = build_canonical_layer()
    df_works = canonical["canonical_works"]
    df_exp = canonical["canonical_expenditures"]
    
    df_exp_feat = compute_expenditure_model_features(df_works, df_exp)
    
    assert "utilization_ratio" in df_exp_feat.columns
    assert "payment_concentration_hhi" in df_exp_feat.columns
    
    # Utilization ratio capped at 1.00 (or 100%)
    assert (df_exp_feat["utilization_ratio"] <= 1.001).all()
    
    # Mathematical reconciliation check
    source_total = float(df_exp["fund_disbursed_amount"].fillna(0.0).sum())
    agg_total = float(df_exp_feat["total_disbursed_amount"].sum())
    assert abs(source_total - agg_total) < 1.0

def test_model4_forecasting_series_continuity():
    """Verify Model 4 monthly forecasting series continuity and reconciliation."""
    canonical = build_canonical_layer()
    df_exp = canonical["canonical_expenditures"]
    
    df_forecast = compute_forecasting_series(df_exp)
    
    assert "state" in df_forecast.columns
    assert "year_month" in df_forecast.columns
    assert "total_disbursed_amount" in df_forecast.columns
    
    source_total = float(df_exp["fund_disbursed_amount"].fillna(0.0).sum())
    forecast_total = float(df_forecast["total_disbursed_amount"].sum())
    assert abs(source_total - forecast_total) < 1.0

def test_sla_policy_constants():
    """Verify SLA policy constants are strictly configured policy values."""
    assert SLA_REC_TO_SANC_DAYS == 75
    assert SLA_REJECTION_DAYS == 45
    assert SLA_COMPLETION_DAYS == 365

def test_rejection_sla_not_currently_evaluable():
    """Verification Check 1: Verify rejection SLA fields are missing in source ledgers, marking rejection SLA NOT CURRENTLY EVALUABLE."""
    canonical = build_canonical_layer()
    df_works = canonical["canonical_works"]
    df_recom = canonical.get("raw_recommended", pd.DataFrame())
    
    assert "rejection_date" not in df_works.columns
    assert "rejection_indicator" not in df_works.columns
    if not df_recom.empty:
        assert "rejection_date" not in df_recom.columns

def test_vendor_hhi_configurable_threshold():
    """Verification Check 2: Verify Vendor HHI formula sum(share^2) and named config threshold VENDOR_HHI_ALERT_THRESHOLD = 0.40."""
    assert VENDOR_HHI_ALERT_THRESHOLD == 0.40
    
    canonical = build_canonical_layer()
    df_exp = canonical["canonical_expenditures"]
    
    res = compute_vendor_agency_risk_features(df_exp)
    df_hhi = res["ida_hhi_summary"]
    pairs = res["ida_vendor_pair_features"]
    
    # Manual mathematical verification of sum(share^2) on first IDA
    sample_ida = df_hhi.iloc[0]["ida"]
    sample_pairs = pairs[pairs["ida"] == sample_ida]
    manual_hhi = float(np.sum(sample_pairs["vendor_share_in_ida"] ** 2))
    assert abs(manual_hhi - df_hhi.iloc[0]["ida_vendor_hhi"]) < 1e-6
    
    # Verify is_high_procurement_risk_ida uses threshold
    expected_flag = df_hhi.iloc[0]["ida_vendor_hhi"] > VENDOR_HHI_ALERT_THRESHOLD
    assert df_hhi.iloc[0]["is_high_procurement_risk_ida"] == expected_flag

def test_logic3_compliance_rule_engine():
    """Verify Logic 3 MP entitlement utilization calculation."""
    canonical = build_canonical_layer()
    df_works = canonical["canonical_works"]
    df_mp = canonical["canonical_mp_allocations"]
    df_cal = canonical["canonical_calamity"]
    df_exp = canonical["canonical_expenditures"]
    
    df_comp = compute_compliance_features(df_works, df_mp, df_cal, df_exp)
    
    assert "mp_name" in df_comp.columns
    assert "entitlement_utilization_pct" in df_comp.columns
    assert "entitlement_exceeded_flag" in df_comp.columns

def test_vendor_agency_risk_analyzer_hhi():
    """Verify Vendor-Agency Risk Analyzer Herfindahl-Hirschman Index (HHI) calculation."""
    canonical = build_canonical_layer()
    df_exp = canonical["canonical_expenditures"]
    
    res = compute_vendor_agency_risk_features(df_exp)
    assert "ida_vendor_pair_features" in res
    assert "vendor_national_features" in res
    assert "ida_hhi_summary" in res
    
    df_hhi = res["ida_hhi_summary"]
    assert "ida_vendor_hhi" in df_hhi.columns
    assert (df_hhi["ida_vendor_hhi"] >= 0.0).all()
    assert (df_hhi["ida_vendor_hhi"] <= 1.001).all()
