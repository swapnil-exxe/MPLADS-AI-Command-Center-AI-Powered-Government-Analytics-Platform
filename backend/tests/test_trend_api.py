# -*- coding: utf-8 -*-
"""
Automated Verification Suite for Trend & Aggregate API Endpoints
MPLADS Problem Statement: MPLADS PS 190942
"""

import pytest


def test_api_national_trends(client, ministry_headers):
    """Validates /api/v1/analytics/trends/national response schema and data integrity."""
    response = client.get("/api/v1/analytics/trends/national", headers=ministry_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert "summary" in data
    assert "quarterly_trends" in data
    assert len(data["quarterly_trends"]) >= 9

    # Check latest quarter properties
    latest_q = data["quarterly_trends"][-1]
    assert "year_quarter" in latest_q
    assert "total_sanctioned_works" in latest_q
    assert "cost_anomaly_rate" in latest_q
    assert "delay_rate" in latest_q
    assert "fund_anomaly_rate" in latest_q
    assert "duplicate_work_rate" in latest_q
    assert latest_q["total_sanctioned_works"] > 0


def test_api_state_trends(client, ministry_headers):
    """Validates /api/v1/analytics/trends/state response schema and benchmark comparison."""
    response = client.get("/api/v1/analytics/trends/state?state=Uttar Pradesh", headers=ministry_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert data["state"] == "Uttar Pradesh"
    assert "national_benchmark_quarter" in data
    assert "trends" in data
    assert len(data["trends"]) > 0

    first_trend = data["trends"][0]
    assert "year_quarter" in first_trend
    assert "credibility_tier" in first_trend


def test_api_district_trends(client, ministry_headers):
    """Validates /api/v1/analytics/trends/district response schema and state peer baseline."""
    response = client.get("/api/v1/analytics/trends/district?state=Bihar&district=PATNA", headers=ministry_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert data["state"] == "Bihar"
    assert data["district"] == "PATNA"
    assert "credibility_tier" in data
    assert "trends" in data
    assert "state_peer_benchmark" in data


def test_api_mp_trends(client, ministry_headers):
    """Validates /api/v1/analytics/trends/mp response schema and tenure summary."""
    response = client.get("/api/v1/analytics/trends/mp?mp_name=Priya", headers=ministry_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert "mp_name" in data
    assert "tenure_summary" in data
    assert "trends" in data
    assert data["tenure_summary"]["tenure_total_works"] > 0


def test_api_early_warnings(client, ministry_headers):
    """Validates /api/v1/analytics/early-warnings endpoint and filtering."""
    response = client.get("/api/v1/analytics/early-warnings?limit=20", headers=ministry_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert "total_alerts" in data
    assert "watchlist_count" in data
    assert "critical_count" in data
    assert "alerts" in data
    assert len(data["alerts"]) <= 20

    if data["alerts"]:
        alert = data["alerts"][0]
        assert "work_id" in alert
        assert "warning_type" in alert
        assert "paradigm" in alert
        assert "urgency_level" in alert
        assert "action_recommended" in alert
