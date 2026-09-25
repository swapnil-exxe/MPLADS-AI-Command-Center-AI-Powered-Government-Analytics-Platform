import re
from typing import Dict, List, Tuple
import pandas as pd
from .config import COLUMN_CANONICAL_MAP

def to_snake_case(text: str) -> str:
    """Converts a column title to canonical snake_case."""
    # Remove currency symbol and parens e.g. ( ₹ )
    s = re.sub(r"[\(（\s]*[₹\$\€\£\¥\w]*[\)）\s]*$", "", text)
    s = re.sub(r"[^\w\s]", "", s).strip()
    s = re.sub(r"[\s\t\n]+", "_", s)
    return s.lower()

def normalize_column_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Remaps DataFrame columns to canonical snake_case names.
    Returns (remapped_df, source_to_canonical_dict).
    """
    df = df.copy()
    mapping = {}
    new_columns = []
    
    seen_cols = {}
    for orig_col in df.columns:
        clean_orig = orig_col.strip()
        if clean_orig in COLUMN_CANONICAL_MAP:
            canonical = COLUMN_CANONICAL_MAP[clean_orig]
        elif orig_col in COLUMN_CANONICAL_MAP:
            canonical = COLUMN_CANONICAL_MAP[orig_col]
        else:
            canonical = to_snake_case(orig_col)
            
        if canonical in seen_cols:
            seen_cols[canonical] += 1
            unique_canonical = f"{canonical}_{seen_cols[canonical]}"
        else:
            seen_cols[canonical] = 0
            unique_canonical = canonical
            
        mapping[orig_col] = unique_canonical
        new_columns.append(unique_canonical)
        
    df.columns = new_columns
    return df, mapping
