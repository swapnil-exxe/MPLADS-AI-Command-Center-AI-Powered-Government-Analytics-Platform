# -*- coding: utf-8 -*-
"""
Automated Verification Suite for Trend & Aggregate Rollup Engine
MPLADS Problem Statement: MPLADS PS 190942
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from analytics.trends.aggregator import (
    assign_credibility_tier,
    empirical_bayes_smoothing,
    compute_trajectory,
    prepare_canonical_work_dataset,
    aggregate_group_quarterly
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ROLLUPS_PATH = DATA_DIR / "model_outputs" / "trends" / "trend_quarterly_rollups.parquet"


def test_credibility_tier_boundaries():
    """Validates sample volume credibility tier assignments."""
    # Quarterly grain
    assert assign_credibility_tier(5, grain="quarter") == "INSUFFICIENT"
    assert assign_credibility_tier(9, grain="quarter") == "INSUFFICIENT"
    assert assign_credibility_tier(10, grain="quarter") == "MODERATE"
    assert assign_credibility_tier(24, grain="quarter") == "MODERATE"
    assert assign_credibility_tier(25, grain="quarter") == "ROBUST"
    assert assign_credibility_tier(100, grain="quarter") == "ROBUST"

    # Fiscal Year grain
    assert assign_credibility_tier(5, grain="fiscal_year") == "INSUFFICIENT"
    assert assign_credibility_tier(15, grain="fiscal_year") == "LOW_VOLUME"
    assert assign_credibility_tier(35, grain="fiscal_year") == "MODERATE"
    assert assign_credibility_tier(60, grain="fiscal_year") == "ROBUST"


def test_empirical_bayes_shrinkage_math():
    """Validates that Empirical Bayes shrinkage pulls small sample proportions toward prior."""
    p_prior = 0.010
    m_weight = 20.0

    # Small sample: 1 out of 2 works anomalous (raw = 50.0%)
    p_smoothed = empirical_bayes_smoothing(k=1, n=2, p_prior=p_prior, m_weight=m_weight)
    # Expected: (1 + 20 * 0.01) / (2 + 20) = 1.2 / 22 = 0.05454...
    assert np.isclose(p_smoothed, 1.2 / 22.0, atol=1e-4)
    assert p_smoothed < 0.10  # Pulled drastically down from 50%

    # Large sample: 25 out of 500 works anomalous (raw = 5.0%)
    p_large = empirical_bayes_smoothing(k=25, n=500, p_prior=p_prior, m_weight=m_weight)
    # Expected: (25 + 0.2) / 520 = 25.2 / 520 = 0.04846...
    assert np.isclose(p_large, 25.2 / 520.0, atol=1e-4)
    assert np.isclose(p_large, 0.050, atol=0.005)  # Preserves large-sample signal


def test_trajectory_classification_logic():
    """Validates trajectory state machine detection."""
    # Insufficient history (< 2)
    assert compute_trajectory([0.05]) == "INSUFFICIENT_HISTORY"

    # Sustained increase (3 strictly increasing periods)
    assert compute_trajectory([0.01, 0.03, 0.06]) == "SUSTAINED_INCREASE"
    assert compute_trajectory([0.02, 0.02, 0.03, 0.05, 0.08]) == "SUSTAINED_INCREASE"

    # Stable (minor noise)
    assert compute_trajectory([0.05, 0.052, 0.049, 0.051]) == "STABLE"

    # Deteriorating (jump of >= +2% absolute and >= 25% relative)
    assert compute_trajectory([0.02, 0.02, 0.02, 0.05]) == "DETERIORATING"

    # Improving (drop of >= -2% absolute and >= -25% relative)
    assert compute_trajectory([0.08, 0.08, 0.08, 0.03]) == "IMPROVING"


def test_rollup_parquet_conservation_and_invariants():
    """Verifies persisted rollup parquet satisfies conservation laws and bounds."""
    assert ROLLUPS_PATH.exists(), f"Rollups file not found at {ROLLUPS_PATH}"
    df = pd.read_parquet(ROLLUPS_PATH)

    assert len(df) > 0
    assert "grain_type" in df.columns
    assert "year_quarter" in df.columns

    # 1. National row count check
    nat_df = df[df["grain_type"] == "NATIONAL"]
    assert len(nat_df) >= 9, "Expected at least 9 national quarters"
    assert (nat_df["total_sanctioned_works"] > 0).all()

    # 2. Bounded rates
    for col in ["cost_anomaly_rate", "fund_anomaly_rate", "delay_rate", "sanction_sla_compliance_rate"]:
        valid_rates = df[col].dropna()
        assert (valid_rates >= 0.0).all()
        assert (valid_rates <= 1.0).all()

    # 3. Work-grain de-duplication assertion
    # Unique duplicate works must never exceed total sanctioned works
    assert (df["unique_duplicate_works_count"] <= df["total_sanctioned_works"]).all()

    # 4. Conservation of works across states per quarter
    state_df = df[df["grain_type"] == "STATE"]
    for q in nat_df["year_quarter"].unique():
        nat_count = nat_df[nat_df["year_quarter"] == q]["total_sanctioned_works"].iloc[0]
        state_count = state_df[state_df["year_quarter"] == q]["total_sanctioned_works"].sum()
        assert nat_count == state_count, f"Conservation failed for quarter {q}: {nat_count} nat vs {state_count} state sum"
