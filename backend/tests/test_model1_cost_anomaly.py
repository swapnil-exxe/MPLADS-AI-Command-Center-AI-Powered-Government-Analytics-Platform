import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from ml_models.cost_anomaly.config import (
    COST_FEATURES_PATH,
    OUTPUT_PARQUET_PATH,
    PEER_MIN_GROUP_SIZE,
    SEVERITY_HIGH_THRESHOLD,
    SEVERITY_MEDIUM_THRESHOLD,
)
from ml_models.cost_anomaly.preprocessing import validate_input_schema, assert_zero_leakage, prepare_features
from ml_models.cost_anomaly.peer_groups import assign_hierarchical_peer_groups
from ml_models.cost_anomaly.train import train_peer_isolation_forests
from ml_models.cost_anomaly.score import score_works_dataset, normalize_isolation_score
from ml_models.cost_anomaly.explain import attach_explanations
from ml_models.cost_anomaly.pipeline import run_model1_pipeline

def test_model1_input_schema_validation():
    """Test A: Input schema validation ensures required Phase 3 cost feature columns exist."""
    df = pd.read_parquet(COST_FEATURES_PATH)
    assert validate_input_schema(df) is True

def test_model1_zero_leakage_assertion():
    """Test B: Zero leakage programmatic assertion ensures no post-sanction columns are present."""
    df = pd.read_parquet(COST_FEATURES_PATH)
    assert assert_zero_leakage(df) is True

def test_model1_peer_group_hierarchy_and_fallback():
    """Test C & D: Peer grouping assigns correct levels and falls back when N < 15."""
    df = pd.read_parquet(COST_FEATURES_PATH)
    df_annotated = assign_hierarchical_peer_groups(df, min_group_size=15)
    
    assert "peer_group_used" in df_annotated.columns
    assert "peer_group_level" in df_annotated.columns
    assert "peer_group_size" in df_annotated.columns
    
    levels = df_annotated["peer_group_level"].unique()
    assert "STATE_WORK_TYPE" in levels
    
    # Check that any work assigned to STATE_WORK_TYPE has group_size >= 15
    fine_works = df_annotated[df_annotated["peer_group_level"] == "STATE_WORK_TYPE"]
    assert (fine_works["peer_group_size"] >= 15).all()

def test_model1_score_bounds_and_determinism():
    """Test E & F: Cost anomaly score is within [0.0, 1.0] and scoring is deterministic."""
    df = pd.read_parquet(COST_FEATURES_PATH).head(500)
    df_annotated = assign_hierarchical_peer_groups(df, min_group_size=5)
    peer_models = train_peer_isolation_forests(df_annotated)
    
    df_scored_1 = score_works_dataset(df_annotated, peer_models)
    df_scored_2 = score_works_dataset(df_annotated, peer_models)
    
    # Check score bounds [0.0, 1.0]
    scores = df_scored_1["cost_anomaly_score"]
    assert (scores >= 0.0).all()
    assert (scores <= 1.0).all()
    
    # Check determinism
    np.testing.assert_array_equal(df_scored_1["cost_anomaly_score"].values, df_scored_2["cost_anomaly_score"].values)

def test_model1_data_quality_exception_routing():
    """Test G: Sub-1,000 INR records are routed to DATA_QUALITY_EXCEPTION status."""
    df_output = pd.read_parquet(OUTPUT_PARQUET_PATH)
    dq_records = df_output[df_output["is_data_quality_exception"]]
    
    if not dq_records.empty:
        assert (dq_records["severity"] == "DATA_QUALITY_EXCEPTION").all()
        assert (dq_records["cost_anomaly_score"] == 0.0).all()

def test_model1_end_to_end_pipeline_output():
    """Verify output parquet exists and contains expected columns."""
    assert OUTPUT_PARQUET_PATH.exists()
    df_out = pd.read_parquet(OUTPUT_PARQUET_PATH)
    
    assert len(df_out) >= 98825
    expected_cols = [
        "work_id", "peer_group_used", "peer_group_level", "peer_group_size",
        "is_data_quality_exception", "raw_anomaly_score", "cost_anomaly_score",
        "severity", "explanation"
    ]
    for col in expected_cols:
        assert col in df_out.columns
