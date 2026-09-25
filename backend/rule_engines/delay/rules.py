import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from .config import DelayConfig

class DelayRulesEngine:
    def __init__(self, config: DelayConfig):
        self.config = config

    def evaluate_recommendation_delay(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Rule 1: RECOMMENDATION_SANCTION_DELAY
        Official SLA: 75 days (MPLADS Guideline Para 3.12).
        Returns: (days, delay_days, severity, normalized_score)
        """
        rec_dates = pd.to_datetime(df["recommended_date"], errors="coerce")
        sanc_dates = pd.to_datetime(df["sanction_date"], errors="coerce")

        days = (sanc_dates - rec_dates).dt.days.values
        # Negative check / data quality assertion
        is_negative = (days < 0)
        days_clean = np.where(is_negative, 0, days)

        delay_days = np.maximum(0, days_clean - self.config.rec_to_sanc_sla_days)

        # Severity
        severity = np.where(
            days_clean > self.config.rec_high_threshold, "HIGH",
            np.where(
                days_clean > self.config.rec_medium_threshold, "MEDIUM",
                np.where(days_clean > self.config.rec_low_threshold, "LOW", "NONE")
            )
        )

        # Normalized Score [0.0, 1.0]
        # <= 75d: maps into [0.0, 0.25]
        # > 75d: scales from 0.25 to 1.0 at rec_max_scale_days (300d)
        ratio = days_clean / float(self.config.rec_to_sanc_sla_days)
        score = np.where(
            ratio <= 1.0,
            0.25 * ratio,
            0.25 + 0.75 * np.minimum(1.0, (days_clean - self.config.rec_to_sanc_sla_days) / float(self.config.rec_max_scale_days - self.config.rec_to_sanc_sla_days))
        )

        return days, delay_days, severity, np.round(score, 4)

    def evaluate_completion_delay(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Rule 2: COMPLETION_DELAY (Completed works only)
        Guideline Limit: 365 days (1 year).
        Returns: (days, delay_days, severity, normalized_score)
        """
        is_completed = df["is_completed_flag"].values == True
        sanc_dates = pd.to_datetime(df["sanction_date"], errors="coerce")
        comp_dates = pd.to_datetime(df["completion_date"], errors="coerce")

        raw_days = (comp_dates - sanc_dates).dt.days.values
        days = np.where(is_completed, raw_days, np.nan)
        delay_days = np.where(is_completed, np.maximum(0, raw_days - self.config.completion_guideline_days), np.nan)

        # Severity (only evaluated for completed works)
        severity = np.where(
            ~is_completed, "NOT_APPLICABLE",
            np.where(
                raw_days > self.config.exec_high_threshold, "HIGH",
                np.where(raw_days > self.config.exec_medium_threshold, "MEDIUM", "NONE")
            )
        )

        # Score [0.0, 1.0]
        # <= 365d: 0.0
        # > 365d: scales from 0.50 to 1.0 at 912 days
        score = np.where(
            ~is_completed, 0.0,
            np.where(
                raw_days <= self.config.completion_guideline_days, 0.0,
                0.50 + 0.50 * np.minimum(1.0, (raw_days - self.config.completion_guideline_days) / float(self.config.exec_max_scale_days - self.config.completion_guideline_days))
            )
        )

        return days, delay_days, severity, np.round(score, 4)

    def evaluate_open_work_aging(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Rule 3: OPEN_WORK_AGING (Incomplete works only)
        Guideline Limit: 365 days (1 year from sanction against fixed reference date).
        Returns: (days, overdue_days, severity, normalized_score)
        """
        is_open = df["is_completed_flag"].values == False
        ref_date = pd.to_datetime(self.config.fixed_reference_date)
        sanc_dates = pd.to_datetime(df["sanction_date"], errors="coerce")

        raw_days = (ref_date - sanc_dates).dt.days.values
        days = np.where(is_open, raw_days, np.nan)
        overdue_days = np.where(is_open, np.maximum(0, raw_days - self.config.completion_guideline_days), np.nan)

        # Severity (only evaluated for incomplete works)
        severity = np.where(
            ~is_open, "NOT_APPLICABLE",
            np.where(
                raw_days > self.config.exec_high_threshold, "HIGH",
                np.where(raw_days > self.config.exec_medium_threshold, "MEDIUM", "NONE")
            )
        )

        # Score [0.0, 1.0]
        score = np.where(
            ~is_open, 0.0,
            np.where(
                raw_days <= self.config.completion_guideline_days, 0.0,
                0.50 + 0.50 * np.minimum(1.0, (raw_days - self.config.completion_guideline_days) / float(self.config.exec_max_scale_days - self.config.completion_guideline_days))
            )
        )

        return days, overdue_days, severity, np.round(score, 4)
