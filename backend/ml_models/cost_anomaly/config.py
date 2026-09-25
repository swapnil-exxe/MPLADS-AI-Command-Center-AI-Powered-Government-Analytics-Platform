from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Input Feature File Path
COST_FEATURES_PATH = DATA_DIR / "features" / "cost" / "cost_anomaly_features.parquet"

# Output Model Outputs Path
MODEL_OUTPUTS_DIR = DATA_DIR / "model_outputs" / "cost_anomaly"
OUTPUT_PARQUET_PATH = MODEL_OUTPUTS_DIR / "cost_anomaly_scores.parquet"

# Model Artifacts Directory Path
MODELS_DIR = BASE_DIR / "models" / "cost_anomaly"
PEER_MODELS_DIR = MODELS_DIR / "peer_models"

# Reports Path
REPORT_PATH = DATA_DIR / "reports" / "model1_cost_anomaly_report.md"

# SLA / Peer Parameters
PEER_MIN_GROUP_SIZE = 15
MODEL_VERSION = "cost_anomaly_v1"

# Hyperparameters for Isolation Forest
RANDOM_STATE = 42
N_ESTIMATORS = 50
CONTAMINATION = 0.05
MAX_SAMPLES = "auto"

# Forbidden Post-Sanction Columns for Zero Leakage Check
LEAKAGE_FORBIDDEN_COLUMNS = [
    "expenditure_date",
    "expenditure_amount",
    "completion_date",
    "payment_status",
    "fund_disbursed_amount",
    "utilization_ratio",
    "total_disbursed_amount",
    "amount_disbursed",
    "image_url",
    "is_completed_flag",
    "first_expenditure_date",
    "last_expenditure_date",
]

# Feature Columns used for Model Training
MODEL_FEATURE_COLS = [
    "sanction_amount_log",
    "peer_iqr_deviation",
    "cost_ratio_vs_peer_median",
    "rec_to_sanc_days",
    "desc_word_count",
]

# Severity Thresholds
SEVERITY_HIGH_THRESHOLD = 0.75
SEVERITY_MEDIUM_THRESHOLD = 0.50
