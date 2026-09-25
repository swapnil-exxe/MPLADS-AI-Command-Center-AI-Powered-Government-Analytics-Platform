# -*- coding: utf-8 -*-
"""
Pydantic Schemas for Trend & Aggregate Analytics and Early Warning Mechanisms
MPLADS Problem Statement: MPLADS PS 190942
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CredibilityTierEnum:
    ROBUST = "ROBUST"
    MODERATE = "MODERATE"
    LOW_VOLUME = "LOW_VOLUME"
    INSUFFICIENT = "INSUFFICIENT"


class TrajectoryEnum:
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DETERIORATING = "DETERIORATING"
    SUSTAINED_INCREASE = "SUSTAINED_INCREASE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


class WarningTypeEnum:
    SLA_SANCTION_CLIFF = "SLA_SANCTION_CLIFF"
    STAGNATION_INCUBATION = "STAGNATION_INCUBATION"
    BATCH_DUPLICATE_CLUSTER = "BATCH_DUPLICATE_CLUSTER"


class UrgencyLevelEnum:
    WATCHLIST = "WATCHLIST"
    CRITICAL = "CRITICAL"


class QuarterTrendItem(BaseModel):
    year_quarter: str
    quarter_start_date: str
    total_sanctioned_works: int
    total_sanctioned_amount: float
    total_disbursed_amount: float
    credibility_tier: str

    # Cost Anomaly (Module 1)
    high_cost_works_count: int
    cost_anomaly_rate: Optional[float]
    excess_sanctioned_amount_inr: float
    cost_trajectory: str

    # Duplicate Works (Module 2 - Work-grain de-duplicated)
    unique_duplicate_works_count: int
    duplicate_work_rate: Optional[float]
    duplicate_cluster_density: float
    duplicate_exposure_inr: float

    # Fund & Expenditure Anomaly (Module 3)
    high_fund_works_count: int
    fund_anomaly_rate: Optional[float]
    status_mismatch_count: int
    dormant_sanction_count: int
    fund_trajectory: str

    # Statutory Delay & SLA (Module 4)
    sanction_sla_compliant_count: int
    sanction_sla_compliance_rate: Optional[float]
    mean_rec_to_sanc_delay_days: float
    high_delay_works_count: int
    delay_rate: Optional[float]
    delay_trajectory: str


class NationalTrendsResponse(BaseModel):
    summary: Dict[str, Any]
    quarterly_trends: List[QuarterTrendItem]


class StateTrendItem(BaseModel):
    state: str
    year_quarter: str
    total_sanctioned_works: int
    total_sanctioned_amount: float
    total_disbursed_amount: float
    credibility_tier: str
    cost_anomaly_rate: Optional[float]
    cost_anomaly_rate_smoothed: Optional[float]
    duplicate_work_rate: Optional[float]
    fund_anomaly_rate: Optional[float]
    delay_rate: Optional[float]
    sanction_sla_compliance_rate: Optional[float]
    cost_trajectory: str
    delay_trajectory: str
    fund_trajectory: str


class StateTrendsResponse(BaseModel):
    state: Optional[str]
    national_benchmark_quarter: Dict[str, Any]
    trends: List[StateTrendItem]


class DistrictTrendItem(BaseModel):
    state: str
    district: str
    year_quarter: str
    total_sanctioned_works: int
    total_sanctioned_amount: float
    total_disbursed_amount: float
    credibility_tier: str
    cost_anomaly_rate: Optional[float]
    cost_anomaly_rate_smoothed: Optional[float]
    duplicate_work_rate: Optional[float]
    fund_anomaly_rate: Optional[float]
    delay_rate: Optional[float]
    sanction_sla_compliance_rate: Optional[float]
    cost_trajectory: str
    delay_trajectory: str
    fund_trajectory: str


class DistrictTrendsResponse(BaseModel):
    state: str
    district: str
    credibility_tier: str
    trends: List[DistrictTrendItem]
    state_peer_benchmark: Dict[str, Any]


class MPTrendItem(BaseModel):
    mp_name: str
    house: Optional[str]
    fiscal_year_or_quarter: str
    total_sanctioned_works: int
    total_sanctioned_amount: float
    total_disbursed_amount: float
    credibility_tier: str
    cost_anomaly_rate: Optional[float]
    duplicate_work_rate: Optional[float]
    fund_anomaly_rate: Optional[float]
    delay_rate: Optional[float]
    sanction_sla_compliance_rate: Optional[float]


class MPTrendsResponse(BaseModel):
    mp_name: str
    house: Optional[str]
    tenure_summary: Dict[str, Any]
    trends: List[MPTrendItem]
    house_benchmark: Dict[str, Any]


class EarlyWarningItem(BaseModel):
    work_id: str
    state: str
    district: str
    mp_name: Optional[str]
    sanction_amount: float
    work_type_template: Optional[str]
    warning_type: str
    paradigm: str  # "STATUTORY" or "STATISTICAL"
    days_elapsed: int
    days_to_statutory_breach: Optional[int]
    urgency_level: str
    action_recommended: str


class EarlyWarningsResponse(BaseModel):
    total_alerts: int
    watchlist_count: int
    critical_count: int
    alerts: List[EarlyWarningItem]
