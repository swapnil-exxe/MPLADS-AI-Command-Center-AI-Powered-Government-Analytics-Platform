from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DelayConfig:
    # Source data paths
    canonical_works_path: Path = Path("data/features/shared/canonical_works.parquet")
    expenditure_features_path: Path = Path("data/features/expenditure/expenditure_anomaly_features.parquet")

    # Output paths
    output_dir: Path = Path("data/model_outputs/delay_rules")
    scores_output_path: Path = Path("data/model_outputs/delay_rules/delay_scores.parquet")
    report_output_path: Path = Path("data/reports/delay_rule_engine_report.md")

    # Fixed Snapshot Reference Date Strategy (latest sanction date in active dataset)
    # Using fixed date guarantees complete reproducibility across runs and environments.
    fixed_reference_date: str = "2026-09-05"

    # Official SLA / Policy Constants (Phase 1 Spec & MPLADS Guidelines Para 3.12)
    rec_to_sanc_sla_days: int = 75
    completion_guideline_days: int = 365

    # Recommendation -> Sanction Multi-tier Thresholds
    rec_low_threshold: int = 75      # > 75d = LOW
    rec_medium_threshold: int = 150  # > 150d (2x SLA) = MEDIUM
    rec_high_threshold: int = 225    # > 225d (3x SLA, >90th pct) = HIGH
    rec_max_scale_days: int = 300    # Reaches 1.0 score at 300d (4x SLA)

    # Execution (Completion & Open Aging) Multi-tier Thresholds
    exec_medium_threshold: int = 365 # > 365d (1 year) = MEDIUM
    exec_high_threshold: int = 545   # > 545d (1.5 years) = HIGH
    exec_max_scale_days: int = 912   # Reaches 1.0 score at 912d (2.5 years)
