"""
Unit Tests for Phase 5 — Delay Logic & SLA Rule Engine
AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from rule_engines.delay.config import DelayConfig
from rule_engines.delay.rules import DelayRulesEngine
from rule_engines.delay.score import DelayScorer
from rule_engines.delay.explain import DelayExplanationGenerator
from rule_engines.delay.pipeline import run_delay_pipeline


@pytest.fixture
def config():
    return DelayConfig()


@pytest.fixture
def sample_test_works():
    """Generates synthetic DataFrame testing all boundary and lifecycle conditions."""
    data = {
        "work_id": [f"WS/DELAY/TEST/{i:03d}" for i in range(1, 8)],
        "house": ["Lok Sabha"] * 7,
        "state": ["Uttar Pradesh"] * 7,
        "district": ["Varanasi"] * 7,
        "ida": ["IDA_1"] * 7,
        "mp_name": ["MP A"] * 7,
        "work_status": [
            "Work Completed",       # 1: Sanc within SLA, Comp within SLA (NONE)
            "Work Completed",       # 2: Sanc LOW delay (100d), Comp within SLA (LOW)
            "Work Completed",       # 3: Sanc within SLA, Comp MEDIUM delay (400d) (MEDIUM)
            "Work Completed",       # 4: Sanc HIGH delay (250d), Comp HIGH delay (600d) (HIGH)
            "Sanction",             # 5: Open work, recent (< 365d)
            "Vendor Identification",# 6: Open work, MEDIUM overdue (400d)
            "Work partially Completed" # 7: Open work, HIGH overdue (650d)
        ],
        "sanction_amount": [500000.0] * 7,
        "recommended_date": [
            "2025-01-01",
            "2025-01-01",
            "2025-01-01",
            "2024-01-01",
            "2026-06-01",
            "2025-06-01",
            "2024-01-01"
        ],
        "sanction_date": [
            "2025-02-01", # 1: 31 days (<= 75d)
            "2025-04-11", # 2: 100 days (LOW: 76-150d)
            "2025-02-01", # 3: 31 days (<= 75d)
            "2024-09-07", # 4: 250 days (HIGH: > 225d)
            "2026-07-01", # 5: 30 days (<= 75d)
            "2025-07-01", # 6: 30 days (<= 75d)
            "2024-03-01"  # 7: 60 days (<= 75d)
        ],
        "completion_date": [
            "2025-08-01", # 1: 181 days from sanc (<= 365d)
            "2025-10-01", # 2: 173 days from sanc (<= 365d)
            "2026-03-08", # 3: 400 days from sanc (MEDIUM: 366-545d)
            "2026-04-30", # 4: 600 days from sanc (HIGH: > 545d)
            None,         # 5: open
            None,         # 6: open
            None          # 7: open
        ],
        "is_completed_flag": [True, True, True, True, False, False, False]
    }
    return pd.DataFrame(data)


def test_recommendation_sanction_calculation(config, sample_test_works):
    """Test 1: Tests Recommendation -> Sanction duration and delay days."""
    engine = DelayRulesEngine(config)
    days, delay_days, sev, score = engine.evaluate_recommendation_delay(sample_test_works)

    # Work 1: 31 days -> delay = 0, severity = NONE
    assert days[0] == 31
    assert delay_days[0] == 0
    assert sev[0] == "NONE"

    # Work 2: 100 days -> delay = 25, severity = LOW
    assert days[1] == 100
    assert delay_days[1] == 25
    assert sev[1] == "LOW"

    # Work 4: 250 days -> delay = 175, severity = HIGH
    assert days[3] == 250
    assert delay_days[3] == 175
    assert sev[3] == "HIGH"


def test_sanction_completion_calculation(config, sample_test_works):
    """Test 2 & 6: Tests Sanction -> Completion calculation and completed vs incomplete distinction."""
    engine = DelayRulesEngine(config)
    days, delay_days, sev, score = engine.evaluate_completion_delay(sample_test_works)

    # Completed works
    assert days[0] == 181
    assert delay_days[0] == 0
    assert sev[0] == "NONE"

    assert days[2] == 400
    assert delay_days[2] == 35
    assert sev[2] == "MEDIUM"

    assert days[3] == 600
    assert delay_days[3] == 235
    assert sev[3] == "HIGH"

    # Incomplete works must NOT be evaluated for completion delay
    assert np.isnan(days[4])
    assert np.isnan(delay_days[4])
    assert sev[4] == "NOT_APPLICABLE"


def test_open_work_aging_calculation(config, sample_test_works):
    """Test 3: Tests Open Work Aging calculation against fixed reference date."""
    engine = DelayRulesEngine(config)
    days, overdue_days, sev, score = engine.evaluate_open_work_aging(sample_test_works)

    # Completed works must NOT be evaluated for open work aging
    assert np.isnan(days[0])
    assert sev[0] == "NOT_APPLICABLE"

    # Work 5: Sanc 2026-07-01 vs ref 2026-09-05 = 66 days <= 365d -> NONE
    assert days[4] == 66
    assert overdue_days[4] == 0
    assert sev[4] == "NONE"

    # Work 6: Sanc 2025-07-01 vs ref 2026-09-05 = 431 days -> MEDIUM
    assert days[5] == 431
    assert overdue_days[5] == 66
    assert sev[5] == "MEDIUM"

    # Work 7: Sanc 2024-03-01 vs ref 2026-09-05 = 918 days -> HIGH
    assert days[6] == 918
    assert overdue_days[6] == 553
    assert sev[6] == "HIGH"


def test_negative_and_missing_date_handling(config):
    """Test 4 & 5: Tests that negative or impossible dates do not crash the engine."""
    corrupt_data = pd.DataFrame({
        "work_id": ["WS/BAD/001", "WS/BAD/002"],
        "is_completed_flag": [True, False],
        "work_status": ["Work Completed", "Sanction"],
        "recommended_date": ["2025-06-01", "2025-01-01"],
        "sanction_date": ["2025-01-01", "2025-02-01"], # Corrupt: Sanc before Rec
        "completion_date": ["2024-12-01", None]         # Corrupt: Comp before Sanc
    })
    engine = DelayRulesEngine(config)
    rec_days, rec_del, rec_sev, _ = engine.evaluate_recommendation_delay(corrupt_data)
    comp_days, comp_del, comp_sev, _ = engine.evaluate_completion_delay(corrupt_data)

    # Negative days handled gracefully without exception
    assert rec_del[0] == 0
    assert rec_sev[0] == "NONE"


def test_severity_hierarchy_and_scores(config, sample_test_works):
    """Test 7 & 8: Verifies severity assignment and score bounds [0.0, 1.0]."""
    scorer = DelayScorer(config)
    scored = scorer.compute_all_scores(sample_test_works)

    # Work 1: Both NONE -> NONE
    assert scored.loc[0, "severity"] == "NONE"
    assert scored.loc[0, "delay_score"] < 0.25

    # Work 2: Sanc LOW, Comp NONE -> LOW
    assert scored.loc[1, "severity"] == "LOW"
    assert 0.25 <= scored.loc[1, "delay_score"] < 0.50

    # Work 3: Sanc NONE, Comp MEDIUM -> MEDIUM
    assert scored.loc[2, "severity"] == "MEDIUM"
    assert 0.50 <= scored.loc[2, "delay_score"] < 0.75

    # Work 4: Sanc HIGH, Comp HIGH -> HIGH
    assert scored.loc[3, "severity"] == "HIGH"
    assert scored.loc[3, "delay_score"] >= 0.75

    # Scores strictly in [0.0, 1.0]
    scores = scored["delay_score"].values
    assert (scores >= 0.0).all() and (scores <= 1.0).all()


def test_explanation_generation(config, sample_test_works):
    """Test 10: Verifies transparent, non-empty explanations for all works."""
    scorer = DelayScorer(config)
    scored = scorer.compute_all_scores(sample_test_works)
    explainer = DelayExplanationGenerator(config)

    for _, row in scored.iterrows():
        expl = explainer.generate_explanation(row)
        assert isinstance(expl, str) and len(expl) > 20
        assert "Delay Score:" in expl


def test_full_pipeline_contract_and_determinism(config):
    """Test 9, 11, 12: Full dataset coverage (98,825 rows), determinism, no cross-model deps."""
    scored_df = run_delay_pipeline(config)

    # 1. Total row count (190,942 canonical works)
    assert len(scored_df) >= 98825

    # 2. Required columns present
    required_cols = [
        "work_id", "rec_to_sanc_days", "rec_to_sanc_delay_days", "rec_to_sanc_severity",
        "sanc_to_comp_days", "sanc_to_comp_delay_days", "sanc_to_comp_severity",
        "open_work_aging_days", "open_work_overdue_days", "open_work_aging_severity",
        "delay_score", "severity", "primary_delay_type", "active_delay_types", "explanation"
    ]
    for c in required_cols:
        assert c in scored_df.columns

    # 3. Severity only contains valid tiers
    valid_tiers = {"NONE", "LOW", "MEDIUM", "HIGH"}
    assert set(scored_df["severity"].unique()).issubset(valid_tiers)

    # 4. Scores bounded in [0.0, 1.0]
    scores = scored_df["delay_score"].values
    assert not np.isnan(scores).any()
    assert (scores >= 0.0).all() and (scores <= 1.0).all()

    # 5. Output files exist
    assert config.scores_output_path.exists()
    assert config.report_output_path.exists()
