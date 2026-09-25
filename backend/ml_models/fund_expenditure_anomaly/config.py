from dataclasses import dataclass, field
from pathlib import Path
from typing import List

@dataclass(frozen=True)
class Model3Config:
    # Source data paths
    features_path: Path = Path("data/features/expenditure/expenditure_anomaly_features.parquet")
    canonical_works_path: Path = Path("data/features/shared/canonical_works.parquet")

    # Output artifact paths
    model_output_dir: Path = Path("data/model_outputs/fund_expenditure_anomaly")
    model_save_dir: Path = Path("models/fund_expenditure_anomaly")
    report_output_path: Path = Path("data/reports/model3_fund_expenditure_report.md")

    scores_output_path: Path = Path("data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet")
    model_joblib_path: Path = Path("models/fund_expenditure_anomaly/isolation_forest.joblib")
    scaler_joblib_path: Path = Path("models/fund_expenditure_anomaly/robust_scaler.joblib")
    metadata_json_path: Path = Path("models/fund_expenditure_anomaly/model_metadata.json")

    # Core & Supporting Features for active spend cohort
    core_features: List[str] = field(default_factory=lambda: [
        "utilization_ratio",
        "log_disbursed_amount",
        "transaction_count_log",
        "days_to_first_disbursement_log",
        "payment_concentration_hhi",
        "spending_window_days_log"
    ])

    # Model Hyperparameters
    n_estimators: int = 150
    contamination: float = 0.03
    max_samples: str = "auto"
    random_state: int = 42
    n_jobs: int = -1

    # Calibrated Sigmoid Scoring Parameters
    # score = 1 / (1 + exp(-k * (s_raw - s_0)))
    sigmoid_k: float = 18.0
    sigmoid_s0: float = 0.0

    # Severity Thresholds (Calibrated Anomaly Strength)
    high_threshold: float = 0.70
    medium_threshold: float = 0.50

    # Deterministic Rule Values
    dormant_sanction_days_threshold: int = 365
    dormant_sanction_score: float = 0.55
    status_mismatch_score: float = 0.85
    low_utilization_completed_score: float = 0.75

    # Phased Multi-Vendor Construction Execution Parameters
    phased_utilization_min: float = 0.85
    phased_min_vendors: int = 3
    phased_max_hhi: float = 0.80
    phased_min_tranches: int = 5
    phased_max_score_cap: float = 0.45

    # Context & Explanation Parameters
    peer_median_tranches: int = 1
    fragmentation_threshold: int = 10
