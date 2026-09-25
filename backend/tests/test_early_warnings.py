# -*- coding: utf-8 -*-
"""
Automated Verification Suite for Early Warning Engine
MPLADS Problem Statement: MPLADS PS 190942
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from analytics.trends.early_warning import (
    generate_sla_cliff_alerts,
    generate_stagnation_incubation_alerts,
    generate_batch_duplicate_cluster_alerts,
    compile_all_early_warnings,
    FIXED_REFERENCE_DATE
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WARNINGS_PATH = DATA_DIR / "model_outputs" / "trends" / "early_warnings_active.parquet"


def test_sla_cliff_boundary_conditions():
    """Validates 45-74 day statutory SLA cliff threshold logic."""
    ref = pd.to_datetime("2026-09-05")
    mock_works = pd.DataFrame([
        {
            "work_id": "W_TOO_EARLY",
            "state": "Bihar", "district": "Patna", "mp_name": "MP 1", "sanction_amount": 100000.0, "work_type_template": "T",
            "recommended_date": "2026-07-25", "sanction_date": "2026-09-05", # 42 days (below 45d threshold)
            "rec_to_sanc_days": 42
        },
        {
            "work_id": "W_WATCHLIST",
            "state": "Bihar", "district": "Patna", "mp_name": "MP 1", "sanction_amount": 100000.0, "work_type_template": "T",
            "recommended_date": "2026-07-15", "sanction_date": "2026-09-05", # 52 days (WATCHLIST: 45-59d)
            "rec_to_sanc_days": 52
        },
        {
            "work_id": "W_CRITICAL",
            "state": "Bihar", "district": "Patna", "mp_name": "MP 1", "sanction_amount": 100000.0, "work_type_template": "T",
            "recommended_date": "2026-07-01", "sanction_date": "2026-09-05", # 66 days (CRITICAL: 60-74d)
            "rec_to_sanc_days": 66
        },
        {
            "work_id": "W_ALREADY_BREACHED",
            "state": "Bihar", "district": "Patna", "mp_name": "MP 1", "sanction_amount": 100000.0, "work_type_template": "T",
            "recommended_date": "2026-06-15", "sanction_date": "2026-09-05", # 82 days (Already breached >75d, not in pre-breach cliff)
            "rec_to_sanc_days": 82
        }
    ])

    alerts = generate_sla_cliff_alerts(mock_works, ref_date=ref)
    alert_ids = {a["work_id"] for a in alerts}

    assert "W_TOO_EARLY" not in alert_ids
    assert "W_WATCHLIST" in alert_ids
    assert "W_CRITICAL" in alert_ids
    assert "W_ALREADY_BREACHED" not in alert_ids

    # Verify urgency tiers
    w_alert = next(a for a in alerts if a["work_id"] == "W_WATCHLIST")
    assert w_alert["urgency_level"] == "WATCHLIST"
    assert w_alert["days_to_statutory_breach"] == 75 - 52  # 23 days

    c_alert = next(a for a in alerts if a["work_id"] == "W_CRITICAL")
    assert c_alert["urgency_level"] == "CRITICAL"
    assert c_alert["days_to_statutory_breach"] == 75 - 66  # 9 days


def test_stagnation_incubation_boundary_conditions():
    """Validates 180-365 day statistical stagnation incubation threshold logic."""
    ref = pd.to_datetime("2026-09-05")
    mock_fund = pd.DataFrame([
        {
            "work_id": "W_RECENT",
            "state": "UP", "district": "Varanasi", "mp_name": "MP 2", "sanction_amount": 500000.0, "work_type_template": "Road",
            "sanction_date": "2026-06-01",  # ~96 days old (< 180d)
            "amount_disbursed": 0.0,
            "work_status": "Sanction"
        },
        {
            "work_id": "W_INCUBATING",
            "state": "UP", "district": "Varanasi", "mp_name": "MP 2", "sanction_amount": 500000.0, "work_type_template": "Road",
            "sanction_date": "2026-01-01",  # ~247 days old (180-365d)
            "amount_disbursed": 0.0,
            "work_status": "Sanction"
        },
        {
            "work_id": "W_ACTIVE_DISBURSED",
            "state": "UP", "district": "Varanasi", "mp_name": "MP 2", "sanction_amount": 500000.0, "work_type_template": "Road",
            "sanction_date": "2026-01-01",  # ~247 days old, but disbursed
            "amount_disbursed": 250000.0,
            "work_status": "Sanction"
        },
        {
            "work_id": "W_DORMANT",
            "state": "UP", "district": "Varanasi", "mp_name": "MP 2", "sanction_amount": 500000.0, "work_type_template": "Road",
            "sanction_date": "2025-01-01",  # > 365 days old (Full dormant sanction, not incubation)
            "amount_disbursed": 0.0,
            "work_status": "Sanction"
        }
    ])

    alerts = generate_stagnation_incubation_alerts(mock_fund, ref_date=ref)
    alert_ids = {a["work_id"] for a in alerts}

    assert "W_RECENT" not in alert_ids
    assert "W_INCUBATING" in alert_ids
    assert "W_ACTIVE_DISBURSED" not in alert_ids
    assert "W_DORMANT" not in alert_ids


def test_early_warnings_persisted_dataset():
    """Validates the live persisted early warnings dataset."""
    assert WARNINGS_PATH.exists()
    df = pd.read_parquet(WARNINGS_PATH)

    assert len(df) > 0
    assert "warning_type" in df.columns
    assert "urgency_level" in df.columns
    assert "paradigm" in df.columns

    # Verify paradigms
    paradigms = df["paradigm"].unique().tolist()
    assert "STATUTORY" in paradigms
    assert "STATISTICAL" in paradigms

    # Urgency levels
    urgencies = df["urgency_level"].unique().tolist()
    assert set(urgencies).issubset({"CRITICAL", "WATCHLIST"})
