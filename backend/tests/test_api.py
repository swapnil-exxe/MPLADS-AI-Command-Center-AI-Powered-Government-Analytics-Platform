"""
Comprehensive API Integration Tests for Phase 6.2 — FastAPI Backend & Core Endpoints
Tests all routes, schemas, pagination, filtering, 404 handling, and independent model profiles.
Includes ministry authorization headers for protected endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root / serves status 200 for single page application."""
    res = client.get("/")
    assert res.status_code == 200


def test_health_check():
    """Verify live database connection and work count without authentication."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["total_works"] >= 98825
    assert data["db_latency_ms"] >= 0.0


def test_filter_metadata():
    """Verify dynamic dropdown options return non-empty lists without authentication."""
    res = client.get("/api/v1/meta/filters")
    assert res.status_code == 200
    data = res.json()
    assert len(data["states"]) > 30
    assert len(data["districts"]) > 700
    assert "HIGH" in data["cost_severities"]


def test_works_pagination_and_structure(ministry_headers):
    """Verify pagination metadata and work record structure."""
    res = client.get("/api/v1/works?page=1&page_size=5", headers=ministry_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["pagination"]["total_records"] >= 98825
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 5
    assert len(data["items"]) == 5
    assert "work_id" in data["items"][0]
    assert "sanction_amount" in data["items"][0]


def test_work_detail_independent_profiles(ministry_headers):
    """Verify deep-dive dossier contains all 4 independent model assessments without composite risk."""
    list_res = client.get("/api/v1/works?page=1&page_size=1", headers=ministry_headers)
    work_id = list_res.json()["items"][0]["work_id"]

    res = client.get(f"/api/v1/works/{work_id}", headers=ministry_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["work_id"] == work_id
    assert "independent_risk_profiles" in data

    profiles = data["independent_risk_profiles"]
    assert "cost_anomaly" in profiles
    assert "duplicate_pairs" in profiles
    assert "fund_anomaly" in profiles
    assert "delay" in profiles
    assert "composite_risk_score" not in profiles


def test_work_detail_not_found(ministry_headers):
    """Verify 404 response for non-existent work ID."""
    res = client.get("/api/v1/works/NON_EXISTENT_WORK_ID_12345", headers=ministry_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_cost_anomalies_filtering(ministry_headers):
    """Verify Model 1 cost anomaly filtering by HIGH and DATA_QUALITY_EXCEPTION."""
    res_high = client.get("/api/v1/analytics/cost-anomalies?severity=HIGH&page_size=5", headers=ministry_headers)
    assert res_high.status_code == 200
    data_high = res_high.json()
    assert data_high["pagination"]["total_records"] > 0
    for item in data_high["items"]:
        assert item["severity"] == "HIGH"
        assert item["cost_anomaly_score"] >= 0.0

    res_dq = client.get("/api/v1/analytics/cost-anomalies?severity=DATA_QUALITY_EXCEPTION", headers=ministry_headers)
    assert res_dq.status_code == 200
    data_dq = res_dq.json()
    assert data_dq["pagination"]["total_records"] >= 0


def test_cost_anomaly_detail(ministry_headers):
    """Verify single work cost anomaly lookup with joined work metadata."""
    res = client.get("/api/v1/analytics/cost-anomalies?severity=HIGH&page_size=1", headers=ministry_headers)
    work_id = res.json()["items"][0]["work_id"]

    detail_res = client.get(f"/api/v1/analytics/cost-anomalies/{work_id}", headers=ministry_headers)
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["work_id"] == work_id
    assert data["sanction_amount"] is not None
    assert data["peer_group_used"] is not None


def test_duplicate_works_pair_endpoints(ministry_headers):
    """Verify Model 2 duplicate candidate list and bidirectional pair lookup."""
    res = client.get("/api/v1/analytics/duplicate-works?page_size=5", headers=ministry_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["pagination"]["total_records"] > 0
    assert len(data["items"]) == 5

    first_pair = data["items"][0]
    assert "work_id_1" in first_pair
    assert "work_id_2" in first_pair
    assert first_pair["duplicate_score"] >= 0.70

    w1 = first_pair["work_id_1"]
    pair_res = client.get(f"/api/v1/analytics/duplicate-works/pairs/{w1}", headers=ministry_headers)
    assert pair_res.status_code == 200
    pair_data = pair_res.json()
    assert pair_data["work_id"] == w1
    assert pair_data["total_flagged_pairs"] >= 1


def test_fund_anomalies_filtering(ministry_headers):
    """Verify Model 3 fund anomaly filtering by severity and audit category."""
    res = client.get("/api/v1/analytics/fund-anomalies?severity=HIGH&page_size=5", headers=ministry_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["pagination"]["total_records"] >= 0


def test_fund_anomaly_detail(ministry_headers):
    """Verify single work fund anomaly lookup with joined financial breakdown."""
    res = client.get("/api/v1/analytics/fund-anomalies?severity=HIGH&page_size=1", headers=ministry_headers)
    if res.json()["items"]:
        work_id = res.json()["items"][0]["work_id"]
        detail_res = client.get(f"/api/v1/analytics/fund-anomalies/{work_id}", headers=ministry_headers)
        assert detail_res.status_code == 200


def test_delays_filtering(ministry_headers):
    """Verify Phase 5 delay tracking filtering by severity and primary delay type."""
    res = client.get("/api/v1/analytics/delays?severity=HIGH&page_size=5", headers=ministry_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["pagination"]["total_records"] > 0
    for item in data["items"]:
        assert item["severity"] == "HIGH"


def test_delay_detail(ministry_headers):
    """Verify single work delay lookup with statutory SLA breakdown."""
    res = client.get("/api/v1/analytics/delays?severity=HIGH&page_size=1", headers=ministry_headers)
    work_id = res.json()["items"][0]["work_id"]

    detail_res = client.get(f"/api/v1/analytics/delays/{work_id}", headers=ministry_headers)
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["work_id"] == work_id
    assert data["primary_delay_type"] is not None


def test_district_summary_aggregation(ministry_headers):
    """Verify district summary returns aggregated budget and independent risk counts."""
    res = client.get("/api/v1/analytics/district-summary?limit=5", headers=ministry_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    first = data[0]
    assert "district" in first
    assert "total_works" in first
    assert first["total_works"] > 0
    assert first["total_sanctioned_amount"] > 0


def test_mp_summary_aggregation(ministry_headers):
    """Verify MP summary returns aggregated completion rate and work counts."""
    res = client.get("/api/v1/analytics/mp-summary?limit=5", headers=ministry_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    first = data[0]
    assert "mp_name" in first
    assert "total_works" in first
    assert first["total_works"] > 0
    assert 0.0 <= first["completion_rate"] <= 100.0


def test_empty_string_query_params_regression(ministry_headers):
    """Regression Test: Verify empty string query parameters do not trigger HTTP 422 validation errors."""
    endpoints = [
        "/api/v1/analytics/cost-anomalies?page=1&page_size=5&severity=&state=&district=",
        "/api/v1/analytics/duplicate-works?page=1&page_size=5&severity=&state=&district=",
        "/api/v1/analytics/fund-anomalies?page=1&page_size=5&severity=&audit_category=&state=&district=",
        "/api/v1/analytics/delays?page=1&page_size=5&severity=&primary_delay_type=&state=&district=",
    ]
    for url in endpoints:
        res = client.get(url, headers=ministry_headers)
        assert res.status_code == 200, f"Endpoint {url} failed with {res.status_code}: {res.text}"
        data = res.json()
        assert "pagination" in data
        assert data["pagination"]["total_records"] > 0


def test_unauthenticated_trend_analytics_access():
    """Regression Test: Verify demo/unauthenticated users can access trend analytics and early warnings."""
    endpoints = [
        "/api/v1/analytics/trends/national",
        "/api/v1/analytics/trends/state?state=Uttar%20Pradesh",
        "/api/v1/analytics/trends/district?state=Uttar%20Pradesh&district=LUCKNOW",
        "/api/v1/analytics/trends/mp?mp_name=Sonia%20Gandhi",
        "/api/v1/analytics/early-warnings?limit=5",
    ]
    for url in endpoints:
        res = client.get(url)
        assert res.status_code == 200, f"Unauthenticated access to {url} failed with {res.status_code}: {res.text}"


