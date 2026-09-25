"""
Unit Tests for Phase 4.3 — Model 3: Fund & Expenditure Anomaly Detection
AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from ml_models.fund_expenditure_anomaly.config import Model3Config
from ml_models.fund_expenditure_anomaly.features import FeatureEngineer
from ml_models.fund_expenditure_anomaly.model import FundIsolationForest
from ml_models.fund_expenditure_anomaly.score import CalibratedScorer
from ml_models.fund_expenditure_anomaly.explain import ExplanationGenerator
from ml_models.fund_expenditure_anomaly.pipeline import run_fund_expenditure_pipeline


@pytest.fixture
def config():
    return Model3Config()


@pytest.fixture
def sample_feature_data():
    """Generates synthetic test DataFrame mimicking expenditure_anomaly_features."""
    data = {
        "work_id": [f"WS/TEST/2024-2025/{i:06d}" for i in range(1, 6)],
        "house": ["Lok Sabha"] * 5,
        "state": ["Uttar Pradesh", "Bihar", "Tamil Nadu", "Maharashtra", "Gujarat"],
        "district": ["Varanasi", "Patna", "Chennai", "Pune", "Ahmedabad"],
        "ida": ["IDA_1", "IDA_2", "IDA_3", "IDA_4", "IDA_5"],
        "mp_name": ["MP A", "MP B", "MP C", "MP D", "MP E"],
        "work_status": [
            "Physical Inspection",       # 1: Active normal
            "Work Completed",            # 2: Active low utilization
            "Vendor Identification",     # 3: Zero-spend recent
            "Work Completed",            # 4: Zero-spend status mismatch
            "Sanction"                   # 5: Zero-spend dormant
        ],
        "sanction_amount": [1000000.0, 2000000.0, 500000.0, 800000.0, 1200000.0],
        "sanction_date": [
            "2025-01-01",
            "2024-06-01",
            "2026-06-01",               # Recent (< 365d)
            "2024-01-01",               # Old completed with zero spend
            "2023-01-01"                # Old sanction with zero spend (> 365d)
        ],
        "total_disbursed_amount": [1000000.0, 400000.0, 0.0, 0.0, 0.0],
        "transaction_count": [1, 2, 0, 0, 0],
        "max_single_payment": [1000000.0, 250000.0, 0.0, 0.0, 0.0],
        "mean_single_payment": [1000000.0, 200000.0, 0.0, 0.0, 0.0],
        "max_payment_ratio": [1.0, 0.625, 0.0, 0.0, 0.0],
        "payment_concentration_hhi": [1.0, 0.54, 0.0, 0.0, 0.0],
        "spending_window_days": [0.0, 45.0, 0.0, 0.0, 0.0],
        "spending_velocity_per_day": [1000000.0, 8888.0, 0.0, 0.0, 0.0],
        "utilization_ratio": [1.0, 0.20, 0.0, 0.0, 0.0],
        "remaining_sanction_balance": [0.0, 1600000.0, 500000.0, 800000.0, 1200000.0],
        "days_to_first_disbursement": [30.0, 180.0, None, None, None]
    }
    return pd.DataFrame(data)


def test_feature_engineering(config, sample_feature_data):
    """Tests feature extraction, scaling, and cohort segregation."""
    fe = FeatureEngineer(config)
    df_all, df_active, df_zero, X_scaled = fe.prepare_data(sample_feature_data)

    assert len(df_active) == 2
    assert len(df_zero) == 3
    assert X_scaled.shape == (2, len(config.core_features))
    assert not np.isnan(X_scaled).any()

    # Verify zero-spend category labeling
    categories = df_zero["zero_spend_category"].tolist()
    assert "NORMAL_AWAITING_DISBURSEMENT" in categories
    assert "STATUS_EXPENDITURE_MISMATCH" in categories
    assert "DORMANT_SANCTION" in categories


def test_calibrated_scorer_bounds(config):
    """Verifies that calibrated anomaly score is strictly in [0.0, 1.0]."""
    scorer = CalibratedScorer(config)
    test_raw_scores = np.array([-1.0, -0.5, -0.19, 0.0, 0.05, 0.15, 1.0])
    calibrated = scorer.calibrate(test_raw_scores)

    assert (calibrated >= 0.0).all() and (calibrated <= 1.0).all()
    # Monotonically increasing
    assert (np.diff(calibrated) > 0).all()
    # Boundary calibration
    assert np.isclose(calibrated[3], 0.50, atol=1e-3) # At raw = 0.0


def test_zero_spend_rules(config, sample_feature_data):
    """Verifies deterministic scoring rules for zero-disbursement works."""
    fe = FeatureEngineer(config)
    df_all, df_active, df_zero, X_scaled = fe.prepare_data(sample_feature_data)

    s_raw_active = np.array([-0.15, -0.05])
    scorer = CalibratedScorer(config)
    scored_df = scorer.score_all(df_active, s_raw_active, df_zero)

    # 1. Normal recent sanction
    recent = scored_df[scored_df["audit_category"] == "NORMAL_AWAITING_DISBURSEMENT"].iloc[0]
    assert recent["fund_anomaly_score"] == 0.0
    assert recent["severity"] == "LOW"

    # 2. Status mismatch (Completed with 0 spend)
    mismatch = scored_df[scored_df["audit_category"] == "STATUS_EXPENDITURE_MISMATCH"].iloc[0]
    assert mismatch["fund_anomaly_score"] == config.status_mismatch_score
    assert mismatch["severity"] == "HIGH"

    # 3. Dormant sanction (> 365 days)
    dormant = scored_df[scored_df["audit_category"] == "DORMANT_SANCTION"].iloc[0]
    assert dormant["fund_anomaly_score"] == config.dormant_sanction_score
    assert dormant["severity"] == "MEDIUM"


def test_active_completed_low_utilization_override(config, sample_feature_data):
    """Verifies that Work Completed with < 50% utilization is boosted to >= 0.75 / HIGH."""
    fe = FeatureEngineer(config)
    df_all, df_active, df_zero, X_scaled = fe.prepare_data(sample_feature_data)

    # Even if model assigned low raw score:
    s_raw_active = np.array([-0.20, -0.20])
    scorer = CalibratedScorer(config)
    scored_df = scorer.score_all(df_active, s_raw_active, df_zero)

    low_util_work = scored_df[scored_df["work_id"] == "WS/TEST/2024-2025/000002"].iloc[0]
    assert low_util_work["fund_anomaly_score"] >= config.low_utilization_completed_score
    assert low_util_work["severity"] == "HIGH"


def test_explanation_generation(config, sample_feature_data):
    """Verifies that non-empty, well-formed explanations are generated for all categories."""
    fe = FeatureEngineer(config)
    df_all, df_active, df_zero, X_scaled = fe.prepare_data(sample_feature_data)
    scorer = CalibratedScorer(config)
    scored_df = scorer.score_all(df_active, np.array([-0.1, 0.1]), df_zero)

    explainer = ExplanationGenerator(config)
    for _, row in scored_df.iterrows():
        reasons, expl = explainer.generate_reasons_and_explanation(row)
        assert isinstance(reasons, list) and len(reasons) > 0
        assert isinstance(expl, str) and len(expl) > 20
        # Check that physical progress percentage claim is not present
        assert "physical progress without financial" not in expl.lower()


def test_full_pipeline_contract(config):
    """Executes full pipeline and verifies output contract across all real records."""
    scored_df = run_fund_expenditure_pipeline(config)

    # 1. Total row count matches input dataset
    assert len(scored_df) == 98825

    # 2. Required columns present
    required_cols = [
        "work_id", "sanction_amount", "total_disbursed_amount", "utilization_ratio",
        "fund_anomaly_score", "severity", "audit_category", "anomaly_reasons", "explanation"
    ]
    for col in required_cols:
        assert col in scored_df.columns

    # 3. Score bounded in [0.0, 1.0] and no NaNs
    scores = scored_df["fund_anomaly_score"].values
    assert not np.isnan(scores).any()
    assert (scores >= 0.0).all() and (scores <= 1.0).all()

    # 4. Severity only contains valid tiers
    valid_severities = {"LOW", "MEDIUM", "HIGH"}
    assert set(scored_df["severity"].unique()).issubset(valid_severities)

    # 5. Output file exists on disk
    assert config.scores_output_path.exists()
    assert config.model_joblib_path.exists()
    assert config.metadata_json_path.exists()
    assert config.report_output_path.exists()
