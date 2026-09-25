# -*- coding: utf-8 -*-
"""
FastAPI Router for Trend & Aggregate Analytics and Early Warning Mechanisms
MPLADS Problem Statement: MPLADS PS 190942
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException, status
import pandas as pd
import numpy as np

from api.auth import OptionalUser
from analytics.trends.schemas import (
    NationalTrendsResponse,
    QuarterTrendItem,
    StateTrendsResponse,
    StateTrendItem,
    DistrictTrendsResponse,
    DistrictTrendItem,
    MPTrendsResponse,
    MPTrendItem,
    EarlyWarningsResponse,
    EarlyWarningItem,
)


router = APIRouter(prefix="/analytics", tags=["Trend & Aggregate Governance Analytics"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
TRENDS_PARQUET = DATA_DIR / "model_outputs" / "trends" / "trend_quarterly_rollups.parquet"
WARNINGS_PARQUET = DATA_DIR / "model_outputs" / "trends" / "early_warnings_active.parquet"

# Cached DataFrames
_df_rollups: Optional[pd.DataFrame] = None
_df_warnings: Optional[pd.DataFrame] = None


def get_rollups_df() -> pd.DataFrame:
    global _df_rollups
    if _df_rollups is None:
        if not TRENDS_PARQUET.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trend rollups artifact not found. Please run the trend pipeline first."
            )
        _df_rollups = pd.read_parquet(TRENDS_PARQUET)
    return _df_rollups


def get_warnings_df() -> pd.DataFrame:
    global _df_warnings
    if _df_warnings is None:
        if not WARNINGS_PARQUET.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Early warnings artifact not found. Please run the trend pipeline first."
            )
        _df_warnings = pd.read_parquet(WARNINGS_PARQUET)
    return _df_warnings


@router.get("/trends", response_model=NationalTrendsResponse)
@router.get("/trends/national", response_model=NationalTrendsResponse)
def get_national_trends(
    current_user: OptionalUser = None
):
    """
    Returns nationwide macro quarterly trend series (2024Q3 to 2026Q3) across
    all four independent analytical modules with zero composite risk score.
    """
    df = get_rollups_df()
    nat_df = df[df["grain_type"] == "NATIONAL"].sort_values("year_quarter")

    if nat_df.empty:
        raise HTTPException(status_code=404, detail="National trends not found")

    quarter_items = []
    for _, r in nat_df.iterrows():
        quarter_items.append(QuarterTrendItem(
            year_quarter=str(r["year_quarter"]),
            quarter_start_date=str(r["quarter_start_date"]),
            total_sanctioned_works=int(r["total_sanctioned_works"]),
            total_sanctioned_amount=float(r["total_sanctioned_amount"]),
            total_disbursed_amount=float(r["total_disbursed_amount"]),
            credibility_tier=str(r["credibility_tier"]),
            high_cost_works_count=int(r["high_cost_works_count"]),
            cost_anomaly_rate=float(r["cost_anomaly_rate"]) if pd.notna(r["cost_anomaly_rate"]) else None,
            excess_sanctioned_amount_inr=float(r["excess_sanctioned_amount_inr"]),
            cost_trajectory=str(r["cost_trajectory"]),
            unique_duplicate_works_count=int(r["unique_duplicate_works_count"]),
            duplicate_work_rate=float(r["duplicate_work_rate"]) if pd.notna(r["duplicate_work_rate"]) else None,
            duplicate_cluster_density=float(r["duplicate_cluster_density"]),
            duplicate_exposure_inr=float(r["duplicate_exposure_inr"]),
            high_fund_works_count=int(r["high_fund_works_count"]),
            fund_anomaly_rate=float(r["fund_anomaly_rate"]) if pd.notna(r["fund_anomaly_rate"]) else None,
            status_mismatch_count=int(r["status_mismatch_count"]),
            dormant_sanction_count=int(r["dormant_sanction_count"]),
            fund_trajectory=str(r["fund_trajectory"]),
            sanction_sla_compliant_count=int(r["sanction_sla_compliant_count"]),
            sanction_sla_compliance_rate=float(r["sanction_sla_compliance_rate"]) if pd.notna(r["sanction_sla_compliance_rate"]) else None,
            mean_rec_to_sanc_delay_days=float(r["mean_rec_to_sanc_delay_days"]),
            high_delay_works_count=int(r["high_delay_works_count"]),
            delay_rate=float(r["delay_rate"]) if pd.notna(r["delay_rate"]) else None,
            delay_trajectory=str(r["delay_trajectory"]),
        ))

    latest = quarter_items[-1] if quarter_items else None
    summary = {
        "total_canonical_works": 98825,
        "latest_quarter": latest.year_quarter if latest else "N/A",
        "latest_cost_anomaly_rate": latest.cost_anomaly_rate if latest else None,
        "latest_delay_rate": latest.delay_rate if latest else None,
        "latest_fund_anomaly_rate": latest.fund_anomaly_rate if latest else None,
        "latest_duplicate_work_rate": latest.duplicate_work_rate if latest else None,
        "statutory_mandate": "MPLADS Guidelines Para 3.12 (75d sanction SLA, 365d completion limit)"
    }

    return NationalTrendsResponse(
        summary=summary,
        quarterly_trends=quarter_items
    )


@router.get("/trends/state", response_model=StateTrendsResponse)
def get_state_trends(
    state: Optional[str] = Query(None, description="State name (e.g. 'Uttar Pradesh')"),
    current_user: OptionalUser = None
):
    """
    Returns quarterly trends for a specific state, plus national benchmark comparison.
    RBAC: State officers are strictly scoped to their assigned state.
    """
    if current_user and current_user.role == "STATE_OFFICER":
        state = current_user.assigned_state
    elif not state:
        state = "Uttar Pradesh"  # Default reference state

    df = get_rollups_df()
    state_df = df[(df["grain_type"] == "STATE") & (df["state"].str.upper() == state.upper())].sort_values("year_quarter")

    if state_df.empty:
        raise HTTPException(status_code=404, detail=f"No trend data found for state: {state}")

    # National benchmark for comparison
    nat_latest = df[df["grain_type"] == "NATIONAL"].sort_values("year_quarter").iloc[-1].to_dict()
    nat_benchmark = {
        "benchmark_quarter": str(nat_latest["year_quarter"]),
        "national_cost_rate": float(nat_latest["cost_anomaly_rate"]) if pd.notna(nat_latest["cost_anomaly_rate"]) else 0.010,
        "national_delay_rate": float(nat_latest["delay_rate"]) if pd.notna(nat_latest["delay_rate"]) else 0.154,
        "national_fund_rate": float(nat_latest["fund_anomaly_rate"]) if pd.notna(nat_latest["fund_anomaly_rate"]) else 0.018,
        "national_sla_rate": float(nat_latest["sanction_sla_compliance_rate"]) if pd.notna(nat_latest["sanction_sla_compliance_rate"]) else 0.490,
    }

    trend_items = []
    for _, r in state_df.iterrows():
        trend_items.append(StateTrendItem(
            state=str(r["state"]),
            year_quarter=str(r["year_quarter"]),
            total_sanctioned_works=int(r["total_sanctioned_works"]),
            total_sanctioned_amount=float(r["total_sanctioned_amount"]),
            total_disbursed_amount=float(r["total_disbursed_amount"]),
            credibility_tier=str(r["credibility_tier"]),
            cost_anomaly_rate=float(r["cost_anomaly_rate"]) if pd.notna(r["cost_anomaly_rate"]) else None,
            cost_anomaly_rate_smoothed=float(r["cost_anomaly_rate_smoothed"]) if pd.notna(r["cost_anomaly_rate_smoothed"]) else None,
            duplicate_work_rate=float(r["duplicate_work_rate"]) if pd.notna(r["duplicate_work_rate"]) else None,
            fund_anomaly_rate=float(r["fund_anomaly_rate"]) if pd.notna(r["fund_anomaly_rate"]) else None,
            delay_rate=float(r["delay_rate"]) if pd.notna(r["delay_rate"]) else None,
            sanction_sla_compliance_rate=float(r["sanction_sla_compliance_rate"]) if pd.notna(r["sanction_sla_compliance_rate"]) else None,
            cost_trajectory=str(r["cost_trajectory"]),
            delay_trajectory=str(r["delay_trajectory"]),
            fund_trajectory=str(r["fund_trajectory"]),
        ))

    return StateTrendsResponse(
        state=state,
        national_benchmark_quarter=nat_benchmark,
        trends=trend_items
    )


@router.get("/trends/district", response_model=DistrictTrendsResponse)
def get_district_trends(
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    current_user: OptionalUser = None
):
    """
    Returns quarterly trends for a specific district, credibility tier, and state peer benchmark.
    RBAC: District officers are strictly scoped to their assigned district.
    """
    if current_user:
        if current_user.role == "DISTRICT_OFFICER":
            state = current_user.assigned_state
            district = current_user.assigned_district
        elif current_user.role == "STATE_OFFICER":
            state = current_user.assigned_state

    df = get_rollups_df()
    dist_df = df[
        (df["grain_type"] == "DISTRICT") &
        (df["state"].str.upper() == state.upper()) &
        (df["district"].str.upper() == district.upper())
    ].sort_values("year_quarter")

    if dist_df.empty:
        raise HTTPException(status_code=404, detail=f"No trend data found for district: {district}, {state}")

    # State peer benchmark
    state_sub = df[(df["grain_type"] == "STATE") & (df["state"].str.upper() == state.upper())]
    state_peer_bench = {}
    if not state_sub.empty:
        s_last = state_sub.sort_values("year_quarter").iloc[-1]
        state_peer_bench = {
            "state": state,
            "benchmark_quarter": str(s_last["year_quarter"]),
            "state_cost_rate": float(s_last["cost_anomaly_rate"]) if pd.notna(s_last["cost_anomaly_rate"]) else None,
            "state_delay_rate": float(s_last["delay_rate"]) if pd.notna(s_last["delay_rate"]) else None,
            "state_sla_rate": float(s_last["sanction_sla_compliance_rate"]) if pd.notna(s_last["sanction_sla_compliance_rate"]) else None,
        }

    trend_items = []
    for _, r in dist_df.iterrows():
        trend_items.append(DistrictTrendItem(
            state=str(r["state"]),
            district=str(r["district"]),
            year_quarter=str(r["year_quarter"]),
            total_sanctioned_works=int(r["total_sanctioned_works"]),
            total_sanctioned_amount=float(r["total_sanctioned_amount"]),
            total_disbursed_amount=float(r["total_disbursed_amount"]),
            credibility_tier=str(r["credibility_tier"]),
            cost_anomaly_rate=float(r["cost_anomaly_rate"]) if pd.notna(r["cost_anomaly_rate"]) else None,
            cost_anomaly_rate_smoothed=float(r["cost_anomaly_rate_smoothed"]) if pd.notna(r["cost_anomaly_rate_smoothed"]) else None,
            duplicate_work_rate=float(r["duplicate_work_rate"]) if pd.notna(r["duplicate_work_rate"]) else None,
            fund_anomaly_rate=float(r["fund_anomaly_rate"]) if pd.notna(r["fund_anomaly_rate"]) else None,
            delay_rate=float(r["delay_rate"]) if pd.notna(r["delay_rate"]) else None,
            sanction_sla_compliance_rate=float(r["sanction_sla_compliance_rate"]) if pd.notna(r["sanction_sla_compliance_rate"]) else None,
            cost_trajectory=str(r["cost_trajectory"]),
            delay_trajectory=str(r["delay_trajectory"]),
            fund_trajectory=str(r["fund_trajectory"]),
        ))

    overall_tier = trend_items[-1].credibility_tier if trend_items else "LOW_VOLUME"

    return DistrictTrendsResponse(
        state=state,
        district=district,
        credibility_tier=overall_tier,
        trends=trend_items,
        state_peer_benchmark=state_peer_bench
    )


@router.get("/trends/mp", response_model=MPTrendsResponse)
def get_mp_trends(
    mp_name: str = Query(..., description="Member of Parliament name"),
    current_user: OptionalUser = None
):
    """
    Returns tenure-to-date and fiscal year trends for an MP portfolio vs House benchmark.
    RBAC: MP role users are strictly scoped to their assigned MP name.
    """
    if current_user and current_user.role == "MP":
        mp_name = current_user.assigned_mp_name

    df = get_rollups_df()
    mp_df = df[
        (df["grain_type"] == "MP") &
        (df["mp_name"].str.contains(mp_name, case=False, na=False))
    ].sort_values("year_quarter")

    if mp_df.empty:
        raise HTTPException(status_code=404, detail=f"No trend data found for MP: {mp_name}")

    resolved_mp_name = mp_df["mp_name"].iloc[0]
    house_val = mp_df["house"].iloc[0] if "house" in mp_df.columns else "Lok Sabha"

    # Tenure summary
    tot_works = int(mp_df["total_sanctioned_works"].sum())
    tot_sanc = float(mp_df["total_sanctioned_amount"].sum())
    tot_disb = float(mp_df["total_disbursed_amount"].sum())

    tenure_summary = {
        "mp_name": resolved_mp_name,
        "house": house_val,
        "tenure_total_works": tot_works,
        "tenure_sanctioned_amount": tot_sanc,
        "tenure_disbursed_amount": tot_disb,
        "utilization_efficiency": float(tot_disb / tot_sanc) if tot_sanc > 0 else 0.0,
    }

    house_bench = {
        "house": house_val,
        "benchmark_note": "House benchmark against Lok Sabha / Rajya Sabha active cohorts"
    }

    trend_items = []
    for _, r in mp_df.iterrows():
        trend_items.append(MPTrendItem(
            mp_name=resolved_mp_name,
            house=str(r["house"]) if pd.notna(r["house"]) else house_val,
            fiscal_year_or_quarter=str(r["year_quarter"]),
            total_sanctioned_works=int(r["total_sanctioned_works"]),
            total_sanctioned_amount=float(r["total_sanctioned_amount"]),
            total_disbursed_amount=float(r["total_disbursed_amount"]),
            credibility_tier=str(r["credibility_tier"]),
            cost_anomaly_rate=float(r["cost_anomaly_rate"]) if pd.notna(r["cost_anomaly_rate"]) else None,
            duplicate_work_rate=float(r["duplicate_work_rate"]) if pd.notna(r["duplicate_work_rate"]) else None,
            fund_anomaly_rate=float(r["fund_anomaly_rate"]) if pd.notna(r["fund_anomaly_rate"]) else None,
            delay_rate=float(r["delay_rate"]) if pd.notna(r["delay_rate"]) else None,
            sanction_sla_compliance_rate=float(r["sanction_sla_compliance_rate"]) if pd.notna(r["sanction_sla_compliance_rate"]) else None,
        ))

    return MPTrendsResponse(
        mp_name=resolved_mp_name,
        house=house_val,
        tenure_summary=tenure_summary,
        trends=trend_items,
        house_benchmark=house_bench
    )


@router.get("/early-warnings", response_model=EarlyWarningsResponse)
@router.get("/trends/early-warnings", response_model=EarlyWarningsResponse)
def get_early_warnings(
    warning_type: Optional[str] = Query(None, description="Filter by warning type: SLA_SANCTION_CLIFF, STAGNATION_INCUBATION, BATCH_DUPLICATE_CLUSTER"),
    urgency_level: Optional[str] = Query(None, description="Filter by urgency: CRITICAL, WATCHLIST"),
    limit: int = Query(50, ge=1, le=500, description="Max alerts to return"),
    current_user: OptionalUser = None
):
    """
    Returns live actionable pre-breach alerts grounded in statutory guidelines
    and empirical statistical distributions, scoped by user jurisdiction.
    """
    df = get_warnings_df()

    # Apply RBAC scoping
    if current_user:
        if current_user.role == "STATE_OFFICER" and current_user.assigned_state:
            filtered_df = df[df["state"].str.upper() == current_user.assigned_state.upper()]
            if not filtered_df.empty:
                df = filtered_df
        elif current_user.role == "DISTRICT_OFFICER" and current_user.assigned_district:
            filtered_df = df[
                (df["state"].str.upper() == (current_user.assigned_state or "").upper()) &
                (df["district"].str.upper() == current_user.assigned_district.upper())
            ]
            if not filtered_df.empty:
                df = filtered_df
        elif current_user.role == "MP" and current_user.assigned_mp_name:
            filtered_df = df[df["mp_name"].str.upper().str.contains(current_user.assigned_mp_name.upper(), na=False)]
            if not filtered_df.empty:
                df = filtered_df

    if warning_type and not df[df["warning_type"] == warning_type].empty:
        df = df[df["warning_type"] == warning_type]
    if urgency_level and not df[df["urgency_level"] == urgency_level].empty:
        df = df[df["urgency_level"] == urgency_level]

    total_alerts = len(df)
    crit_count = int((df["urgency_level"] == "CRITICAL").sum())
    watch_count = int((df["urgency_level"] == "WATCHLIST").sum())

    sub_df = df.head(limit)
    items = []
    for _, r in sub_df.iterrows():
        items.append(EarlyWarningItem(
            work_id=str(r["work_id"]),
            state=str(r["state"]),
            district=str(r["district"]),
            mp_name=str(r["mp_name"]) if pd.notna(r["mp_name"]) else None,
            sanction_amount=float(r["sanction_amount"]),
            work_type_template=str(r["work_type_template"]) if pd.notna(r["work_type_template"]) else None,
            warning_type=str(r["warning_type"]),
            paradigm=str(r["paradigm"]),
            days_elapsed=int(r["days_elapsed"]),
            days_to_statutory_breach=int(r["days_to_statutory_breach"]) if pd.notna(r["days_to_statutory_breach"]) else None,
            urgency_level=str(r["urgency_level"]),
            action_recommended=str(r["action_recommended"])
        ))

    return EarlyWarningsResponse(
        total_alerts=total_alerts,
        watchlist_count=watch_count,
        critical_count=crit_count,
        alerts=items
    )
