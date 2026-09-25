from typing import Tuple, Dict, Any, Optional
import pandas as pd
from .config import IDA_DISTRICT_REGEX

def extract_district_from_ida(ida_val: Any) -> Optional[str]:
    """
    Extracts district title before the first '(' in IDA string.
    Example: 'ARARIA(DISTRICT PLANNING OFFICER ARARIA_IDA)' -> 'ARARIA'
    """
    if pd.isna(ida_val) or ida_val is None:
        return None
    s = str(ida_val).strip()
    if not s or s.lower() in ("nan", "null"):
        return None
        
    match = IDA_DISTRICT_REGEX.match(s)
    if match:
        district_str = match.group(1).strip().upper()
        if district_str:
            return district_str
    return None

def normalize_geography_in_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Extracts 'district' from 'ida' column if present.
    Tracks extraction success and failure statistics.
    """
    df = df.copy()
    stats = {
        "has_ida_column": False,
        "success_count": 0,
        "fail_count": 0,
        "unique_districts": 0,
    }
    
    if "ida" in df.columns:
        stats["has_ida_column"] = True
        districts = []
        success_count = 0
        fail_count = 0
        
        for raw_ida in df["ida"]:
            if pd.isna(raw_ida) or str(raw_ida).strip() == "":
                districts.append(None)
                continue
                
            dist = extract_district_from_ida(raw_ida)
            if dist is not None:
                districts.append(dist)
                success_count += 1
            else:
                districts.append(None)
                fail_count += 1
                
        df["district"] = districts
        unique_dists = set(d for d in districts if d is not None)
        
        stats["success_count"] = success_count
        stats["fail_count"] = fail_count
        stats["unique_districts"] = len(unique_dists)
    else:
        df["district"] = None
        
    return df, stats
