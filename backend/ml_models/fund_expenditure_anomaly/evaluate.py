import pandas as pd
import numpy as np
from typing import Dict, Any

class Model3Evaluator:
    def evaluate(self, scored_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates score percentiles, severity breakdown, and audit cohort distributions."""
        total_works = len(scored_df)
        severity_counts = scored_df["severity"].value_counts().to_dict()
        severity_pct = {k: round(v / total_works * 100, 2) for k, v in severity_counts.items()}

        active_mask = (scored_df["audit_category"] == "ACTIVE_EXPENDITURE")
        active_scores = scored_df.loc[active_mask, "fund_anomaly_score"]

        percentiles = [0.0, 0.25, 0.50, 0.75, 0.90, 0.95, 0.97, 0.99, 1.0]
        active_pct_dist = {
            f"p{int(p*100)}": round(float(active_scores.quantile(p)), 4)
            for p in percentiles
        }

        category_counts = scored_df["audit_category"].value_counts().to_dict()

        # Top 10 anomalies for audit review
        top10 = scored_df.sort_values("fund_anomaly_score", ascending=False).head(10)[
            ["work_id", "state", "work_status", "sanction_amount", "total_disbursed_amount",
             "utilization_ratio", "transaction_count", "fund_anomaly_score", "severity", "explanation"]
        ].to_dict(orient="records")

        return {
            "total_works": total_works,
            "active_works_count": int(active_mask.sum()),
            "zero_spend_works_count": int((~active_mask).sum()),
            "severity_counts": severity_counts,
            "severity_pct": severity_pct,
            "active_score_percentiles": active_pct_dist,
            "audit_category_counts": category_counts,
            "top_anomalies_sample": top10
        }
