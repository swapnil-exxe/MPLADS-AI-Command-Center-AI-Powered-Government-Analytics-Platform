from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
REPORTS_DIR = DATA_DIR / "reports"

# Subdirectories for feature outputs
SHARED_FEATURES_DIR = FEATURES_DIR / "shared"
COST_FEATURES_DIR = FEATURES_DIR / "cost"
EXPENDITURE_FEATURES_DIR = FEATURES_DIR / "expenditure"
DUPLICATE_FEATURES_DIR = FEATURES_DIR / "duplicate"
FORECAST_FEATURES_DIR = FEATURES_DIR / "forecasting"
LOGIC_FEATURES_DIR = FEATURES_DIR / "logic"
COMPLIANCE_FEATURES_DIR = FEATURES_DIR / "compliance"
VENDOR_FEATURES_DIR = FEATURES_DIR / "vendor"

# Finalized Phase 1 SLA Policy Constants (in days)
SLA_REC_TO_SANC_DAYS = 75
SLA_REJECTION_DAYS = 45
SLA_COMPLETION_DAYS = 365

# Peer Grouping Fallback Parameters (Model 1)
PEER_MIN_GROUP_SIZE = 15

# Duplicate Candidate Blocking Parameters (Model 2)
DUPLICATE_BLOCKING_WINDOW_DAYS = 90
DUPLICATE_AMOUNT_RATIO_THRESHOLD = 0.90

# Vendor Risk Threshold (Model/Risk Indicator Threshold, Not Legal Threshold)
VENDOR_HHI_ALERT_THRESHOLD = 0.40

# Snapshots Date for Snapshot Calculations
SNAPSHOT_DATE = "2026-09-06"
