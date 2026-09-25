import re
from typing import Tuple, Dict, Any, Optional
import pandas as pd

RAW_AMOUNT_COLUMNS = [
    "recommended_amount_raw",
    "sanction_amount_raw",
    "amount_disbursed_raw",
    "fund_disbursed_amount_raw",
    "allocated_amount_raw",
    "consent_amount_raw",
]

def parse_monetary_amount(val: Any) -> Optional[float]:
    """
    Parses currency string (e.g., '41,76,59,96,002.88', '₹ 497,185.00') into float64.
    Returns None if missing or unparseable.
    """
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "null", "n/a", "none"):
        return None
        
    # Remove currency symbols, commas, spaces
    clean = re.sub(r"[^\d.-]", "", s)
    if not clean or clean == "-" or clean == ".":
        return None
        
    try:
        amt = float(clean)
        return amt
    except ValueError:
        return None

def normalize_amounts_in_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalizes raw amount columns into numeric float64 columns.
    Example: sanction_amount_raw -> sanction_amount.
    Collects statistics (min, max, success_count, fail_count).
    """
    df = df.copy()
    stats = {}
    
    for raw_col in RAW_AMOUNT_COLUMNS:
        if raw_col in df.columns:
            clean_col = raw_col.replace("_raw", "")
            parsed_vals = []
            success_count = 0
            fail_count = 0
            failed_samples = []
            
            for raw_val in df[raw_col]:
                if pd.isna(raw_val) or str(raw_val).strip() == "" or str(raw_val).lower() in ("nan", "null"):
                    parsed_vals.append(None)
                    continue
                    
                parsed_amt = parse_monetary_amount(raw_val)
                if parsed_amt is not None:
                    parsed_vals.append(parsed_amt)
                    success_count += 1
                else:
                    parsed_vals.append(None)
                    fail_count += 1
                    if len(failed_samples) < 5:
                        failed_samples.append(str(raw_val))
                        
            df[clean_col] = parsed_vals
            
            valid_series = [v for v in parsed_vals if v is not None]
            min_val = float(min(valid_series)) if valid_series else None
            max_val = float(max(valid_series)) if valid_series else None
            
            stats[clean_col] = {
                "success_count": success_count,
                "fail_count": fail_count,
                "min_value": min_val,
                "max_value": max_val,
                "failed_samples": failed_samples,
            }
            
    return df, stats
