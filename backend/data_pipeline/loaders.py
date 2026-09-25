import os
from pathlib import Path
from typing import Tuple, Dict, Any, List
import pandas as pd

from .config import DATASET_PATTERNS, ORIGINAL_DATA_DIR
from .lineage import attach_lineage_metadata

def classify_dataset_file(file_name: str) -> str:
    """Classifies a CSV filename into a standard dataset category."""
    name_lower = file_name.lower()
    for cat, patterns in DATASET_PATTERNS.items():
        for pat in patterns:
            import re
            if re.search(pat, name_lower):
                return cat
    return "other"

def determine_house(folder_name: str, file_name: str) -> str:
    """Determines legislative house from folder or filename."""
    combined = (folder_name + " " + file_name).lower()
    if "loksabha" in combined or "lok sabha" in combined or "ls" in combined:
        return "Lok Sabha"
    elif "rajyasabha" in combined or "rajya sabha" in combined or "rs" in combined:
        return "Rajya Sabha"
    return "Unknown"

def load_csv_with_fallback(file_path: Path) -> pd.DataFrame:
    """Loads CSV trying utf-8, utf-8-sig, and latin1 encodings."""
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc, dtype=str, low_memory=False)
            return df
        except Exception:
            continue
    raise ValueError(f"Unable to read CSV file {file_path} with standard encodings.")

def strip_grand_total_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Identifies and removes footer rows where column 0 or 'Sr. No.' equals 'Grand Total'.
    Returns (cleaned_df, grand_total_removed_count).
    """
    if df.empty:
        return df, 0
    
    first_col = df.columns[0]
    # Check if first column value contains "Grand Total"
    is_grand_total = df[first_col].astype(str).str.strip().str.lower().str.contains("grand total", na=False)
    
    removed_count = is_grand_total.sum()
    df_clean = df[~is_grand_total].copy()
    return df_clean, int(removed_count)

from .config import (
    DATASET_PATTERNS,
    ORIGINAL_DATA_DIR,
    ACTIVE_DATASETS,
    OPTIONAL_HISTORICAL_DATASETS,
    ENABLE_HISTORICAL_PROCESSING,
)

def discover_raw_files(
    base_dir: Path = ORIGINAL_DATA_DIR,
    include_historical: bool = ENABLE_HISTORICAL_PROCESSING
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Discovers CSV files under data/original/ subdirectories based on active dataset scope.
    Returns (file_list, dataset_scope_status).
    """
    file_list = []
    scope_status = {}
    
    target_folders = list(ACTIVE_DATASETS)
    if include_historical:
        target_folders.extend(OPTIONAL_HISTORICAL_DATASETS)

    for folder_name in target_folders:
        folder_path = base_dir / folder_name
        if not folder_path.exists():
            scope_status[folder_name] = {
                "is_active": folder_name in ACTIVE_DATASETS,
                "status": "skipped_directory_missing",
                "file_count": 0
            }
            continue
            
        csv_files = list(folder_path.glob("*.csv"))
        if not csv_files:
            scope_status[folder_name] = {
                "is_active": folder_name in ACTIVE_DATASETS,
                "status": "skipped_no_source_files",
                "file_count": 0,
                "message": "No source files currently available. Skipped without error."
            }
            continue
            
        scope_status[folder_name] = {
            "is_active": folder_name in ACTIVE_DATASETS,
            "status": "processed",
            "file_count": len(csv_files)
        }
        
        for path in csv_files:
            f = path.name
            dataset_cat = classify_dataset_file(f)
            house_name = determine_house(folder_name, f)
            file_list.append({
                "path": path,
                "folder": folder_name,
                "filename": f,
                "dataset_category": dataset_cat,
                "house": house_name,
                "size_bytes": path.stat().st_size
            })
            
    # Track unselected optional historical datasets
    if not include_historical:
        for hist_folder in OPTIONAL_HISTORICAL_DATASETS:
            scope_status[hist_folder] = {
                "is_active": False,
                "status": "excluded_optional_historical",
                "file_count": 0,
                "message": "Optional historical dataset excluded from current active scope."
            }

    return file_list, scope_status
