import numpy as np
import pandas as pd
from typing import Tuple
from .config import Model3Config

class CalibratedScorer:
    def __init__(self, config: Model3Config):
        self.config = config

    def calibrate(self, s_raw: np.ndarray) -> np.ndarray:
        """
        Maps raw Isolation Forest score to calibrated relative anomaly strength in [0.0, 1.0]
        using a sigmoid centered at decision boundary s_0:
        score = 1 / (1 + exp(-k * (s_raw - s_0)))
        """
        z = -self.config.sigmoid_k * (s_raw - self.config.sigmoid_s0)
        # Avoid numerical overflow
        z = np.clip(z, -30.0, 30.0)
        return 1.0 / (1.0 + np.exp(z))

    def assign_severity(self, scores: np.ndarray) -> np.ndarray:
        """Maps calibrated anomaly strength to standardized severity tiers."""
        severities = np.where(
            scores >= self.config.high_threshold,
            "HIGH",
            np.where(scores >= self.config.medium_threshold, "MEDIUM", "LOW")
        )
        return severities

    def score_all(
        self,
        df_active: pd.DataFrame,
        s_raw_active: np.ndarray,
        df_zero: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Integrates ML calibrated scores for active works with deterministic audit rules for
        status mismatches and zero-spend cohorts into a single unified dataframe.
        """
        df_active = df_active.copy()
        df_zero = df_zero.copy()

        # Active works scoring
        scores_active = self.calibrate(s_raw_active)
        df_active["raw_score"] = s_raw_active
        df_active["fund_anomaly_score"] = scores_active

        # Active works rule adjustments:
        # 1. Work Completed with utilization < 50% is a confirmed completion-expenditure gap
        is_completed_low_util = (
            (df_active["work_status"] == "Work Completed") &
            (df_active["utilization_ratio"] < 0.50)
        )
        df_active.loc[is_completed_low_util, "fund_anomaly_score"] = np.maximum(
            df_active.loc[is_completed_low_util, "fund_anomaly_score"],
            self.config.low_utilization_completed_score
        )
        df_active["is_completed_low_util"] = is_completed_low_util

        # 2. Early status with large disbursements (> ₹50L while in Sanction / Vendor Identification)
        is_early_high_disb = (
            df_active["work_status"].isin(["Sanction", "Time Estimation"]) &
            (df_active["total_disbursed_amount"] > 0)
        )
        df_active["is_early_high_disb"] = is_early_high_disb

        # 3. Legitimate Multi-Vendor Phased Construction Adjustment
        # Projects with high fund utilization (>= 85%), multiple vendors (>= 3),
        # distributed payments (HHI <= 0.80), and reasonable first-disbursement latency (<= 300d)
        # reflect standard milestone-based civil works execution, not suspicious fragmentation.
        is_healthy_phased = (
            (df_active["utilization_ratio"] >= self.config.phased_utilization_min) &
            (df_active["vendor_count"] >= self.config.phased_min_vendors) &
            (df_active["payment_concentration_hhi"] <= self.config.phased_max_hhi) &
            (df_active["transaction_count"] >= self.config.phased_min_tranches) &
            (df_active["days_to_first_disbursement"].fillna(0.0) <= 300)
        )
        df_active.loc[is_healthy_phased, "fund_anomaly_score"] = np.minimum(
            df_active.loc[is_healthy_phased, "fund_anomaly_score"],
            self.config.phased_max_score_cap
        )
        df_active["is_healthy_phased"] = is_healthy_phased

        df_active["severity"] = self.assign_severity(df_active["fund_anomaly_score"].values)
        df_active["audit_category"] = "ACTIVE_EXPENDITURE"

        # Zero-spend works scoring
        scores_zero = np.zeros(len(df_zero), dtype=float)
        severities_zero = np.array(["LOW"] * len(df_zero), dtype=object)

        is_mismatch = (df_zero["zero_spend_category"] == "STATUS_EXPENDITURE_MISMATCH")
        is_dormant = (df_zero["zero_spend_category"] == "DORMANT_SANCTION")

        scores_zero[is_mismatch] = self.config.status_mismatch_score
        severities_zero[is_mismatch] = "HIGH"

        scores_zero[is_dormant] = self.config.dormant_sanction_score
        severities_zero[is_dormant] = "MEDIUM"

        df_zero["raw_score"] = 0.0
        df_zero["fund_anomaly_score"] = scores_zero
        df_zero["severity"] = severities_zero
        df_zero["audit_category"] = df_zero["zero_spend_category"]
        df_zero["is_completed_low_util"] = False
        df_zero["is_early_high_disb"] = False
        df_zero["is_healthy_phased"] = False

        # Combine
        combined = pd.concat([df_active, df_zero], ignore_index=True)
        return combined
