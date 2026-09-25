import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ORIGINAL_DATA_DIR = DATA_DIR / "original"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
HISTORICAL_PROCESSED_DIR = PROCESSED_DATA_DIR / "_historical"
REPORTS_DIR = DATA_DIR / "reports"

# Active vs Historical Scope Configuration
ACTIVE_DATASETS = ["LokSabha18", "RajyaSabha_Sitting"]
OPTIONAL_HISTORICAL_DATASETS = ["LokSabha17", "RajyaSabha_Retired"]

# Toggle to enable historical processing if explicitly requested
ENABLE_HISTORICAL_PROCESSING = False

# Dataset Category Patterns
DATASET_PATTERNS = {
    "mp_allocations": [r"allocated[\s_]+limit"],
    "calamity": [r"calamity"],
    "expenditures": [r"expenditure"],
    "works_completed": [r"works[\s_]+completed"],
    "works_recommended": [r"works[\s_]+recommended"],
    "works_sanctioned": [r"works[\s_]+sanctioned"],
}

# Regex for Work ID extraction
# Example: WS/\t MP620/2024-2025/133166-Construction...
# Pattern matches: WS/<optional space/tab>MP<digits>/<YYYY>-<YYYY>/<serial>
WORK_ID_REGEX = re.compile(r"WS/\s*MP\d+/\d{4}-\d{4}/\d+", re.IGNORECASE)

# Regex for District extraction from IDA
# Example: GHAZIABAD(DISTRICT MAGISTRAE GHAZIABAD_IDA) -> GHAZIABAD
# Example: ARARIA(DISTRICT PLANNING OFFICER ARARIA_IDA) -> ARARIA
IDA_DISTRICT_REGEX = re.compile(r"^\s*([^(]+?)\s*(?:\(|$)", re.IGNORECASE)

# Column Canonical Name Mapping
# Standardizing varied source column names across 17th/18th Lok Sabha & Rajya Sabha CSVs
COLUMN_CANONICAL_MAP = {
    "Sr. No.": "sr_no",
    "Sr.No.": "sr_no",
    "Work Category": "work_category",
    "Work category": "work_category",
    "Work": "work_raw",
    "WORK": "work_raw",
    "State": "state",
    "IDA": "ida",
    "Hon'ble Members of Parliament": "mp_name",
    "Hon'ble Members of Parliaments": "mp_name",
    "Hon'ble Member of Parliament": "mp_name",
    "Constituency": "constituency",
    "Work Description": "work_description",
    "Work description": "work_description",
    "Recommended date": "recommended_date",
    "RECOMMENDED AMOUNT   ( ₹ )": "recommended_amount_raw",
    "RECOMMENDED AMOUNT ( ₹ )": "recommended_amount_raw",
    "Recommended Amount ( ₹ )": "recommended_amount_raw",
    "Sanction Date": "sanction_date",
    "Sanction Amount ( ₹ )": "sanction_amount_raw",
    "Work Status": "work_status",
    "Image": "image_url",
    "Completion Date": "completion_date",
    "Amount Disbursed ( ₹ )": "amount_disbursed_raw",
    "Work ID": "work_id_raw",
    "Expenditure Date": "expenditure_date",
    "Vendor Name": "vendor_name",
    "Payment Status": "payment_status",
    "Fund Disbursed Amount ( ₹ )": "fund_disbursed_amount_raw",
    "Allocated AMOUNT ( ₹ )": "allocated_amount_raw",
    "Allocated Amount ( ₹ )": "allocated_amount_raw",
    "Calamity Type": "calamity_type",
    "Calamity Name": "calamity_name",
    "Date of Consent": "date_of_consent",
    "Consent Amount ( ₹ )": "consent_amount_raw",
}
