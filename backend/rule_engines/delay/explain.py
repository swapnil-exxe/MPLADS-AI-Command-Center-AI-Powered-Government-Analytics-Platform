import pandas as pd
from typing import List, Tuple
from .config import DelayConfig

def _safe_int(val, default: int = 0) -> int:
    if pd.isna(val) or val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

class DelayExplanationGenerator:
    def __init__(self, config: DelayConfig):
        self.config = config

    def generate_explanation(self, row: pd.Series) -> str:
        """Generates transparent, auditable human-readable narrative citing exact timeline numbers."""
        parts = []

        rec_days = _safe_int(row.get("rec_to_sanc_days", 0))
        rec_delay = _safe_int(row.get("rec_to_sanc_delay_days", 0))
        rec_sev = str(row.get("rec_to_sanc_severity", "NONE"))

        is_completed = bool(row.get("is_completed_flag", False))
        status = str(row.get("work_status", "Unknown"))

        # 1. Recommendation narrative
        if rec_delay > 0:
            parts.append(
                f"Recommendation took {rec_days} days to sanction "
                f"(exceeds 75-day official SLA by {rec_delay} days [{rec_sev}])"
            )
        else:
            parts.append(f"Sanctioned within 75-day SLA ({rec_days} days)")

        # 2. Execution / Aging narrative
        if is_completed:
            comp_days = _safe_int(row.get("sanc_to_comp_days", 0))
            comp_delay = _safe_int(row.get("sanc_to_comp_delay_days", 0))
            comp_sev = str(row.get("sanc_to_comp_severity", "NONE"))
            if comp_delay > 0:
                parts.append(
                    f"Completed in {comp_days} days from sanction "
                    f"(exceeds 365-day guideline by {comp_delay} days [{comp_sev}])"
                )
            else:
                parts.append(f"Completed within 1-year guideline ({comp_days} days)")
        else:
            aging_days = _safe_int(row.get("open_work_aging_days", 0))
            overdue_days = _safe_int(row.get("open_work_overdue_days", 0))
            aging_sev = str(row.get("open_work_aging_severity", "NONE"))
            if overdue_days > 0:
                parts.append(
                    f"Open work ({status}) elapsed {aging_days} days without completion "
                    f"(overdue by {overdue_days} days beyond 365-day limit [{aging_sev}])"
                )
            else:
                parts.append(f"Open work ({status}) active within 365-day limit ({aging_days} days elapsed)")

        score = float(row.get("delay_score", 0.0))
        severity = str(row.get("severity", "NONE"))

        return f"Delay Score: {score:.2f} ({severity}). " + " | ".join(parts)
