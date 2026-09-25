import pandas as pd
import numpy as np
from typing import Dict, Any

class DelayEvaluator:
    def evaluate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Computes comprehensive evaluation metrics and distribution profiles for delay rules."""
        total_works = len(df)
        sev_counts = df["severity"].value_counts().to_dict()
        sev_pct = {k: round(v / total_works * 100, 2) for k, v in sev_counts.items()}

        scores = df["delay_score"]
        score_percentiles = {
            f"p{int(p*100)}": round(float(scores.quantile(p)), 4)
            for p in [0.0, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 1.0]
        }

        # Rule specific breakdowns
        rec_exceeded_count = int((df["rec_to_sanc_delay_days"] > 0).sum())
        comp_mask = df["is_completed_flag"] == True
        comp_exceeded_count = int((df.loc[comp_mask, "sanc_to_comp_delay_days"] > 0).sum())
        open_mask = df["is_completed_flag"] == False
        open_overdue_count = int((df.loc[open_mask, "open_work_overdue_days"] > 0).sum())

        top10_delayed = df.sort_values("delay_score", ascending=False).head(10)[
            ["work_id", "state", "work_status", "rec_to_sanc_days", "sanc_to_comp_days",
             "open_work_aging_days", "delay_score", "severity", "explanation"]
        ].to_dict(orient="records")

        return {
            "total_works": total_works,
            "severity_counts": sev_counts,
            "severity_pct": sev_pct,
            "score_percentiles": score_percentiles,
            "completed_works_count": int(comp_mask.sum()),
            "open_works_count": int(open_mask.sum()),
            "rec_sla_exceeded_count": rec_exceeded_count,
            "rec_sla_exceeded_pct": round(rec_exceeded_count / total_works * 100, 2),
            "comp_guideline_exceeded_count": comp_exceeded_count,
            "comp_guideline_exceeded_pct": round(comp_exceeded_count / comp_mask.sum() * 100, 2) if comp_mask.sum() > 0 else 0.0,
            "open_overdue_count": open_overdue_count,
            "open_overdue_pct": round(open_overdue_count / open_mask.sum() * 100, 2) if open_mask.sum() > 0 else 0.0,
            "top10_delayed_sample": top10_delayed
        }
