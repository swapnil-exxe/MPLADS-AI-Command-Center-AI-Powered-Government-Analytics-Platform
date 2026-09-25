import re
from typing import Tuple, Optional, Any
import pandas as pd
from .config import WORK_ID_REGEX

def extract_and_normalize_work_id(val: Any) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Extracts and normalizes Work ID from raw Work field or Work ID column.
    
    Returns:
        (normalized_work_id, work_type_template, is_na_recommendation)
        
    Example inputs:
      - "WS/\t MP620/2024-2025/133166-Construction of buildings..."
        -> ("WS/MP620/2024-2025/133166", "Construction of buildings...", False)
      - "NA-Construction of Community Hall"
        -> (None, "Construction of Community Hall", True)
      - "WS/MP18070/2025-2026/201278"
        -> ("WS/MP18070/2025-2026/201278", None, False)
    """
    if pd.isna(val) or val is None:
        return None, None, False
        
    s = str(val).strip()
    if not s:
        return None, None, False
        
    if s.startswith("NA-") or s.startswith("NA -"):
        work_type = s.split("-", 1)[1].strip() if "-" in s else s
        return None, work_type, True
        
    match = WORK_ID_REGEX.search(s)
    if match:
        matched_str = match.group(0)
        # Normalize: strip internal tabs and whitespace around slashes/parts
        # e.g., "WS/\t MP620/2024-2025/133166" -> "WS/MP620/2024-2025/133166"
        clean_id = re.sub(r"\s+", "", matched_str).upper()
        
        # Extract template if present after '-'
        work_type = None
        if "-" in s:
            # find text after matched Work ID and '-'
            remainder = s[match.end():]
            if remainder.startswith("-"):
                work_type = remainder[1:].strip()
        return clean_id, work_type, False
        
    return None, None, False

def apply_work_id_processing(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Applies Work ID extraction and normalization across the DataFrame.
    Looks for 'work_id_raw' or 'work_raw'.
    
    Creates columns:
      - work_id: normalized Work ID string or None
      - work_type_template: extracted template text if present
      - is_na_recommendation: boolean flag
    """
    df = df.copy()
    
    target_col = None
    if "work_id_raw" in df.columns:
        target_col = "work_id_raw"
    elif "work_raw" in df.columns:
        target_col = "work_raw"
        
    if not target_col:
        df["work_id"] = None
        df["work_type_template"] = None
        df["is_na_recommendation"] = False
        stats = {
            "total_rows": len(df),
            "valid_work_ids": 0,
            "null_work_ids": len(df),
            "na_recommendations": 0,
        }
        return df, stats
        
    work_ids = []
    templates = []
    na_flags = []
    
    for val in df[target_col]:
        wid, tmpl, is_na = extract_and_normalize_work_id(val)
        work_ids.append(wid)
        templates.append(tmpl)
        na_flags.append(is_na)
        
    df["work_id"] = work_ids
    df["work_type_template"] = templates
    df["is_na_recommendation"] = na_flags
    
    valid_count = sum(1 for w in work_ids if w is not None)
    null_count = sum(1 for w in work_ids if w is None)
    na_count = sum(1 for n in na_flags if n)
    
    stats = {
        "total_rows": len(df),
        "valid_work_ids": valid_count,
        "null_work_ids": null_count,
        "na_recommendations": na_count,
    }
    return df, stats
