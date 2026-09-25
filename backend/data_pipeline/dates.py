from typing import Tuple, Dict, Any, List, Optional
import pandas as pd

DATE_COLUMNS = [
    "recommended_date",
    "sanction_date",
    "completion_date",
    "expenditure_date",
    "date_of_consent",
]

def parse_date_string(val: Any) -> Optional[str]:
    """
    Parses date string e.g. '21-Aug-2026', '2026-08-21' into ISO 'YYYY-MM-DD'.
    Returns None if parsing fails or input is null/empty.
    """
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "null", "n/a", "none"):
        return None
        
    try:
        dt = pd.to_datetime(s, format="%d-%b-%Y", errors="raise")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
        
    try:
        dt = pd.to_datetime(s, errors="raise")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

def normalize_dates_in_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalizes date columns in DataFrame to YYYY-MM-DD strings.
    Collects parse statistics for each present date column.
    """
    df = df.copy()
    stats = {}
    
    for col in DATE_COLUMNS:
        if col in df.columns:
            parsed_list = []
            success_count = 0
            fail_count = 0
            failed_samples = []
            
            for raw_val in df[col]:
                if pd.isna(raw_val) or str(raw_val).strip() == "" or str(raw_val).lower() in ("nan", "null"):
                    parsed_list.append(None)
                    continue
                
                parsed_str = parse_date_string(raw_val)
                if parsed_str is not None:
                    parsed_list.append(parsed_str)
                    success_count += 1
                else:
                    parsed_list.append(None)
                    fail_count += 1
                    if len(failed_samples) < 5:
                        failed_samples.append(str(raw_val))
                        
            df[col] = parsed_list
            stats[col] = {
                "success_count": success_count,
                "fail_count": fail_count,
                "failed_samples": failed_samples,
            }
            
    return df, stats
