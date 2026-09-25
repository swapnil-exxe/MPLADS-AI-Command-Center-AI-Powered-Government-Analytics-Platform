import pandas as pd
import numpy as np
from typing import Dict, Any
from .config import DelayConfig
from .rules import DelayRulesEngine

class DelayScorer:
    def __init__(self, config: DelayConfig):
        self.config = config
        self.engine = DelayRulesEngine(config)

    def compute_all_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluates all rules, computes individual and composite delay scores,
        and determines standardized severity across all works.
        """
        df = df.copy()

        # Rule 1: Recommendation -> Sanction
        rec_days, rec_delay_days, rec_sev, rec_score = self.engine.evaluate_recommendation_delay(df)
        df["rec_to_sanc_days"] = rec_days
        df["rec_to_sanc_delay_days"] = rec_delay_days
        df["rec_to_sanc_severity"] = rec_sev
        df["rec_to_sanc_score"] = rec_score

        # Rule 2: Completion Delay
        comp_days, comp_delay_days, comp_sev, comp_score = self.engine.evaluate_completion_delay(df)
        df["sanc_to_comp_days"] = comp_days
        df["sanc_to_comp_delay_days"] = comp_delay_days
        df["sanc_to_comp_severity"] = comp_sev
        df["sanc_to_comp_score"] = comp_score

        # Rule 3: Open Work Aging
        aging_days, aging_overdue_days, aging_sev, aging_score = self.engine.evaluate_open_work_aging(df)
        df["open_work_aging_days"] = aging_days
        df["open_work_overdue_days"] = aging_overdue_days
        df["open_work_aging_severity"] = aging_sev
        df["open_work_aging_score"] = aging_score

        # Composite Delay Score = max(rec_score, execution_score)
        # Execution score is comp_score if completed, else aging_score
        execution_score = np.where(df["is_completed_flag"] == True, comp_score, aging_score)
        df["execution_delay_score"] = execution_score

        delay_score = np.nan_to_num(np.maximum(rec_score, execution_score), nan=0.0)
        df["delay_score"] = np.round(delay_score, 4)

        # Standardized Severity Hierarchy: HIGH > MEDIUM > LOW > NONE
        # A work's severity is determined by the highest active severity among applicable rules
        severities = np.where(
            (rec_sev == "HIGH") | (comp_sev == "HIGH") | (aging_sev == "HIGH"), "HIGH",
            np.where(
                (rec_sev == "MEDIUM") | (comp_sev == "MEDIUM") | (aging_sev == "MEDIUM"), "MEDIUM",
                np.where((rec_sev == "LOW"), "LOW", "NONE")
            )
        )
        df["severity"] = severities

        # Determine Primary Delay Type
        primary_types = []
        for idx, row in df.iterrows():
            types = []
            if row["rec_to_sanc_delay_days"] > 0:
                types.append("RECOMMENDATION_SANCTION_DELAY")
            if row["is_completed_flag"] and row["sanc_to_comp_delay_days"] > 0:
                types.append("COMPLETION_DELAY")
            elif not row["is_completed_flag"] and row["open_work_overdue_days"] > 0:
                types.append("OPEN_WORK_AGING")
            if not types:
                types.append("ON_SCHEDULE")
            primary_types.append(types)

        df["active_delay_types"] = primary_types
        df["primary_delay_type"] = [t[0] for t in primary_types]

        return df
