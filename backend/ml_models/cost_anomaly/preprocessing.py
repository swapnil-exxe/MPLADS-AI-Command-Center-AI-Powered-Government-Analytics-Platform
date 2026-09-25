import logging
import pandas as pd
import numpy as np
from typing import List, Tuple

from .config import LEAKAGE_FORBIDDEN_COLUMNS, MODEL_FEATURE_COLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def validate_input_schema(df: pd.DataFrame) -> bool:
    """
    Validates that required Phase 3 cost feature columns exist in the DataFrame.
    """
    required = ["work_id", "state", "work_type_template", "sanction_amount", "sanction_amount_log"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Input feature dataset is missing required columns: {missing}")
    logging.info(f"Input schema validated successfully for {len(df):,} works.")
    return True

def assert_zero_leakage(df: pd.DataFrame, feature_cols: List[str] = None) -> bool:
    """
    Programmatically asserts that no forbidden post-sanction columns exist in input DataFrame or feature set.
    """
    cols_to_check = set(df.columns.tolist())
    if feature_cols:
        cols_to_check.update(feature_cols)
        
    detected_leakage = [c for c in LEAKAGE_FORBIDDEN_COLUMNS if c in cols_to_check]
    if detected_leakage:
        raise ValueError(f"ZERO-LEAKAGE FAILURE: Post-sanction columns detected in Model 1 features: {detected_leakage}")
        
    logging.info("Zero-Leakage check PASSED. 0 post-sanction columns detected in Model 1 features.")
    return True

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares finite numeric feature matrix X for Isolation Forest.
    Fills missing values with domain-appropriate defaults.
    """
    X = df.copy()
    
    # Ensure expected numeric features exist or compute default fallbacks
    if "sanction_amount_log" not in X.columns:
        sanc = X["sanction_amount"].fillna(0.0)
        X["sanction_amount_log"] = np.log1p(np.maximum(0.0, sanc))
        
    if "peer_iqr_deviation" not in X.columns:
        X["peer_iqr_deviation"] = 0.0
        
    if "cost_ratio_vs_peer_median" not in X.columns:
        X["cost_ratio_vs_peer_median"] = 1.0
        
    if "rec_to_sanc_days" not in X.columns:
        X["rec_to_sanc_days"] = 0.0
        
    if "desc_word_count" not in X.columns:
        if "work_description" in X.columns:
            X["desc_word_count"] = X["work_description"].fillna("").astype(str).apply(lambda s: len(s.split()))
        else:
            X["desc_word_count"] = 0.0
            
    # Extract numerical feature columns
    feature_matrix = pd.DataFrame(index=df.index)
    for col in MODEL_FEATURE_COLS:
        if col in X.columns:
            feature_matrix[col] = pd.to_numeric(X[col], errors="coerce").fillna(0.0)
        else:
            feature_matrix[col] = 0.0
            
    # Clean infinities
    feature_matrix = feature_matrix.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return feature_matrix
