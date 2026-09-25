# -*- coding: utf-8 -*-
"""
Analytical Rollup Engine for Trend & Aggregate Analytics
MPLADS Problem Statement: MPLADS PS 190942

Implements deterministic multi-tiered aggregation across National, State, District,
and MP entities over Quarterly and Fiscal Year timelines.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


def assign_credibility_tier(n: int, grain: str = "quarter") -> str:
    """
    Assigns sample size credibility tier based on empirical distribution.
    Quarter grain:
      N >= 25 -> ROBUST (top quartile of district-quarters, 100% of states)
      10 <= N < 25 -> MODERATE
      N < 10 -> INSUFFICIENT (rates suppressed)
    Fiscal year / Tenure grain:
      N >= 50 -> ROBUST
      20 <= N < 50 -> MODERATE
      10 <= N < 20 -> LOW_VOLUME
      N < 10 -> INSUFFICIENT
    """
    if grain == "quarter":
        if n >= 25:
            return "ROBUST"
        elif n >= 10:
            return "MODERATE"
        else:
            return "INSUFFICIENT"
    else:
        if n >= 50:
            return "ROBUST"
        elif n >= 20:
            return "MODERATE"
        elif n >= 10:
            return "LOW_VOLUME"
        else:
            return "INSUFFICIENT"


def empirical_bayes_smoothing(
    k: int,
    n: int,
    p_prior: float = 0.010,
    m_weight: float = 10.0
) -> float:
    """
    Applies Empirical Bayes shrinkage toward the benchmark prior proportion:
    p_tilde = (k + M * p_prior) / (n + M)
    """
    if n <= 0:
        return float(p_prior)
    return float((k + m_weight * p_prior) / (n + m_weight))


def compute_trajectory(
    series: List[Optional[float]],
    min_periods: int = 2
) -> str:
    """
    Evaluates trajectory over a sequential list of rates up to the current point:
    - SUSTAINED_INCREASE: strictly increasing over last 3 periods
    - DETERIORATING: current period >= +2.0% absolute and >= +25% relative vs trailing 4-period moving median
    - IMPROVING: current period <= -2.0% absolute and <= -25% relative vs trailing 4-period moving median
    - STABLE: fluctuation within noise band
    - INSUFFICIENT_HISTORY: fewer than min_periods valid entries
    """
    valid_vals = [v for v in series if v is not None and not np.isnan(v)]
    if len(valid_vals) < min_periods:
        return "INSUFFICIENT_HISTORY"

    current = valid_vals[-1]

    # Check sustained increase across last 3 periods
    if len(valid_vals) >= 3:
        if valid_vals[-1] > valid_vals[-2] > valid_vals[-3]:
            return "SUSTAINED_INCREASE"

    # Trailing baseline (up to 4 preceding periods)
    trailing = valid_vals[-5:-1] if len(valid_vals) > 1 else []
    if not trailing:
        return "STABLE"

    baseline = float(np.median(trailing))
    delta = current - baseline

    if baseline > 0.001:
        rel_change = delta / baseline
    else:
        rel_change = 1.0 if delta > 0.02 else 0.0

    if delta >= 0.02 and rel_change >= 0.25:
        return "DETERIORATING"
    elif delta <= -0.02 and rel_change <= -0.25:
        return "IMPROVING"
    else:
        return "STABLE"


def prepare_canonical_work_dataset(
    df_works: pd.DataFrame,
    df_cost: pd.DataFrame,
    df_fund: pd.DataFrame,
    df_delay: pd.DataFrame,
    df_dup: pd.DataFrame
) -> pd.DataFrame:
    """
    Consolidates work metadata with binary indicators and continuous metrics
    from all four analytical modules without post-sanction data leakage.
    De-duplicates Model 2 candidate pairs into unique work-level participation.
    """
    df = df_works.copy()

    # Temporal derivations
    df["sanc_dt"] = pd.to_datetime(df["sanction_date"], errors="coerce")
    df["rec_dt"] = pd.to_datetime(df["recommended_date"], errors="coerce")
    df["year_quarter"] = df["sanc_dt"].dt.to_period("Q").astype(str)
    df["quarter_start_date"] = df["sanc_dt"].dt.to_period("Q").dt.start_time.dt.strftime("%Y-%m-%d")

    # Fiscal year calculation (April 1 - March 31)
    def to_fy(dt):
        if pd.isna(dt):
            return None
        year = dt.year if dt.month >= 4 else dt.year - 1
        return f"FY{year}-{str(year + 1)[-2:]}"

    df["fiscal_year"] = df["sanc_dt"].apply(to_fy)

    # 1. Cost Anomaly (Module 1)
    cost_cols = ["work_id", "severity", "cost_anomaly_score"]
    if "excess_sanction_amount" in df_cost.columns:
        cost_cols.append("excess_sanction_amount")
    elif "peer_median" in df_cost.columns and "sanction_amount" in df_cost.columns:
        df_cost["excess_sanction_amount"] = np.maximum(
            0.0, df_cost["sanction_amount"] - df_cost["peer_median"]
        )
        cost_cols.append("excess_sanction_amount")

    df_c = df_cost[cost_cols].rename(columns={
        "severity": "cost_severity",
        "cost_anomaly_score": "cost_score"
    })
    df = df.merge(df_c, on="work_id", how="left")
    df["is_high_cost"] = df["cost_severity"] == "HIGH"
    if "excess_sanction_amount" not in df.columns:
        df["excess_sanction_amount"] = 0.0
    else:
        df["excess_sanction_amount"] = df["excess_sanction_amount"].fillna(0.0)

    # 2. Duplicate Works (Module 2) - Work-grain de-duplication
    high_dup = df_dup[df_dup["severity"] == "HIGH"]
    dup_counts = pd.concat([high_dup["work_id_1"], high_dup["work_id_2"]]).value_counts().rename("dup_pair_count")
    dup_df = dup_counts.reset_index()
    dup_df.columns = ["work_id", "dup_pair_count"]

    df = df.merge(dup_df, on="work_id", how="left")
    df["dup_pair_count"] = df["dup_pair_count"].fillna(0).astype(int)
    df["is_duplicate_work"] = df["dup_pair_count"] > 0

    # 3. Fund & Expenditure Anomaly (Module 3)
    fund_cols = ["work_id", "severity", "fund_anomaly_score", "audit_category"]
    df_f = df_fund[fund_cols].rename(columns={
        "severity": "fund_severity",
        "fund_anomaly_score": "fund_score"
    })
    df = df.merge(df_f, on="work_id", how="left")
    df["is_high_fund"] = df["fund_severity"] == "HIGH"
    df["is_status_mismatch"] = df["audit_category"] == "STATUS_EXPENDITURE_MISMATCH"
    df["is_dormant_sanction"] = df["audit_category"] == "DORMANT_SANCTION"

    # 4. Statutory Delay (Module 4)
    delay_cols = ["work_id", "severity", "delay_score", "rec_to_sanc_days", "rec_to_sanc_delay_days"]
    df_d = df_delay[delay_cols].rename(columns={
        "severity": "delay_severity"
    })
    df = df.merge(df_d, on="work_id", how="left")
    df["is_high_delay"] = df["delay_severity"] == "HIGH"
    df["is_sanction_sla_compliant"] = (df["rec_to_sanc_days"] >= 0) & (df["rec_to_sanc_days"] <= 75)
    df["rec_to_sanc_delay_days"] = df["rec_to_sanc_delay_days"].fillna(0).astype(int)

    return df


def aggregate_group_quarterly(
    group_df: pd.DataFrame,
    national_prior_cost: float = 0.010,
    m_shrinkage: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Aggregates an entity group into sequential quarterly trend records with
    sample credibility tiers and Empirical Bayes smoothing.
    """
    quarters = sorted(group_df["year_quarter"].dropna().unique())
    results = []

    cost_rates = []
    fund_rates = []
    delay_rates = []

    for q in quarters:
        q_df = group_df[group_df["year_quarter"] == q]
        n = len(q_df)
        if n == 0:
            continue

        q_start = q_df["quarter_start_date"].iloc[0]
        tot_sanc_amt = float(q_df["sanction_amount"].fillna(0).sum())
        tot_disb_amt = float(q_df["amount_disbursed"].fillna(0).sum())

        cred_tier = assign_credibility_tier(n, grain="quarter")

        # Counts
        k_cost = int(q_df["is_high_cost"].sum())
        k_dup = int(q_df["is_duplicate_work"].sum())
        tot_dup_pairs = int(q_df["dup_pair_count"].sum())
        k_fund = int(q_df["is_high_fund"].sum())
        k_mismatch = int(q_df["is_status_mismatch"].sum())
        k_dormant = int(q_df["is_dormant_sanction"].sum())
        k_sla_comp = int(q_df["is_sanction_sla_compliant"].sum())
        k_delay = int(q_df["is_high_delay"].sum())

        mean_delay_days = float(q_df["rec_to_sanc_delay_days"].mean()) if n > 0 else 0.0
        excess_cost = float(q_df[q_df["is_high_cost"]]["excess_sanction_amount"].sum())
        dup_exposure = float(q_df[q_df["is_duplicate_work"]]["sanction_amount"].fillna(0).sum())

        # Duplicate cluster density (pairs / unique works)
        dup_density = float(tot_dup_pairs / k_dup) if k_dup > 0 else 0.0

        # Rate calculations (Suppressed to None if N < 10 for statistical honesty)
        if n >= 10:
            rate_cost = float(k_cost / n)
            rate_dup = float(k_dup / n)
            rate_fund = float(k_fund / n)
            rate_delay = float(k_delay / n)
            rate_sla = float(k_sla_comp / n)
        else:
            rate_cost = None
            rate_dup = None
            rate_fund = None
            rate_delay = None
            rate_sla = None

        # Empirical Bayes smoothed cost rate
        rate_cost_smoothed = empirical_bayes_smoothing(k_cost, n, national_prior_cost, m_shrinkage)

        cost_rates.append(rate_cost)
        fund_rates.append(rate_fund)
        delay_rates.append(rate_delay)

        traj_cost = compute_trajectory(cost_rates)
        traj_fund = compute_trajectory(fund_rates)
        traj_delay = compute_trajectory(delay_rates)

        results.append({
            "year_quarter": q,
            "quarter_start_date": q_start,
            "total_sanctioned_works": n,
            "total_sanctioned_amount": tot_sanc_amt,
            "total_disbursed_amount": tot_disb_amt,
            "credibility_tier": cred_tier,
            "high_cost_works_count": k_cost,
            "cost_anomaly_rate": rate_cost,
            "cost_anomaly_rate_smoothed": rate_cost_smoothed,
            "excess_sanctioned_amount_inr": excess_cost,
            "cost_trajectory": traj_cost,
            "unique_duplicate_works_count": k_dup,
            "duplicate_work_rate": rate_dup,
            "duplicate_cluster_density": dup_density,
            "duplicate_exposure_inr": dup_exposure,
            "high_fund_works_count": k_fund,
            "fund_anomaly_rate": rate_fund,
            "status_mismatch_count": k_mismatch,
            "dormant_sanction_count": k_dormant,
            "fund_trajectory": traj_fund,
            "sanction_sla_compliant_count": k_sla_comp,
            "sanction_sla_compliance_rate": rate_sla,
            "mean_rec_to_sanc_delay_days": mean_delay_days,
            "high_delay_works_count": k_delay,
            "delay_rate": rate_delay,
            "delay_trajectory": traj_delay,
        })

    return results
