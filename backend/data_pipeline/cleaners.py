from typing import Tuple, Dict, Any
import pandas as pd

TEXT_COLUMNS_TO_TRIM = [
    "state",
    "mp_name",
    "constituency",
    "work_category",
    "work_status",
    "payment_status",
    "vendor_name",
    "calamity_type",
    "calamity_name",
]

def clean_text_fields_in_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Trims leading/trailing whitespace and normalizes internal multiple spaces in categorical text fields.
    Collects unique value counts and distributions for key categorical columns.
    """
    df = df.copy()
    distributions = {}
    
    for col in TEXT_COLUMNS_TO_TRIM:
        if col in df.columns:
            # Clean string values
            cleaned_series = df[col].astype(str).apply(
                lambda x: " ".join(x.split()) if pd.notna(x) and x.lower() not in ("nan", "none", "null") else None
            )
            df[col] = cleaned_series
            
            # Value distribution stats (top 20)
            val_counts = cleaned_series.value_counts(dropna=True).head(20).to_dict()
            distributions[col] = {
                "unique_count": int(cleaned_series.nunique(dropna=True)),
                "null_count": int(cleaned_series.isna().sum()),
                "top_value_counts": val_counts
            }
            
    return df, distributions
