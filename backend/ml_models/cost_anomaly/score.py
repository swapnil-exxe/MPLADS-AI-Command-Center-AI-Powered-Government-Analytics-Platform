import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from .config import (
    SEVERITY_HIGH_THRESHOLD,
    SEVERITY_MEDIUM_THRESHOLD,
)
from .preprocessing import prepare_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def normalize_isolation_score(raw_scores: np.ndarray) -> np.ndarray:
    """
    Normalizes raw Isolation Forest decision scores into [0.0, 1.0] interval.
    Raw decision score is negative decision_function (-df).
    Uses calibrated sigmoid transformation centered at decision boundary 0.0.
    """
    val = 1.0 / (1.0 + np.exp(-10.0 * raw_scores))
    return np.clip(val, 0.0, 1.0)

def compute_severity_vector(scores: np.ndarray, is_dq_flags: np.ndarray, is_suff_flags: np.ndarray) -> List[str]:
    """
    Vectorized categorization of severity into application-level review flags.
    """
    severities = []
    for sc, dq, suff in zip(scores, is_dq_flags, is_suff_flags):
        if dq:
            severities.append("DATA_QUALITY_EXCEPTION")
        elif not suff:
            severities.append("INSUFFICIENT_PEER_DATA")
        elif sc >= SEVERITY_HIGH_THRESHOLD:
            severities.append("HIGH")
        elif sc >= SEVERITY_MEDIUM_THRESHOLD:
            severities.append("MEDIUM")
        else:
            severities.append("LOW")
    return severities

def score_works_dataset(
    df_annotated: pd.DataFrame,
    peer_models: Dict[str, Dict[str, Any]]
) -> pd.DataFrame:
    """
    Computes raw and normalized cost anomaly scores for all sanctioned works.
    Uses vectorized per-group inference for fast scoring.
    """
    logging.info("Scoring dataset with trained peer Isolation Forests...")
    
    out = df_annotated.copy()
    
    out["raw_anomaly_score"] = 0.0
    out["cost_anomaly_score"] = 0.0
    out["model_peer_median_amount"] = out.get("peer_median_amount", 0.0).fillna(0.0)
    out["model_peer_iqr_amount"] = out.get("peer_iqr_amount", 0.0).fillna(0.0)
    
    # Vectorized scoring by peer group
    for group_name, group_data in out.groupby("peer_group_used"):
        model_info = peer_models.get(group_name)
        if not model_info:
            continue
            
        clf = model_info["model"]
        indices = group_data.index
        
        # Prepare feature matrix for the group
        X_group = prepare_features(group_data)
        
        # Vectorized decision_function call for all works in the group
        raw_dec = clf.decision_function(X_group)
        raw_scores = -raw_dec
        norm_scores = normalize_isolation_score(raw_scores)
        
        out.loc[indices, "raw_anomaly_score"] = raw_scores
        out.loc[indices, "cost_anomaly_score"] = norm_scores
        out.loc[indices, "model_peer_median_amount"] = model_info["peer_median_amount"]
        out.loc[indices, "model_peer_iqr_amount"] = model_info["peer_iqr_amount"]
        
    # Handle Data Quality Exceptions explicitly
    dq_mask = out["is_data_quality_exception"]
    out.loc[dq_mask, "raw_anomaly_score"] = 0.0
    out.loc[dq_mask, "cost_anomaly_score"] = 0.0
    
    # Compute severities
    out["severity"] = compute_severity_vector(
        out["cost_anomaly_score"].values,
        out["is_data_quality_exception"].values,
        out["is_sufficient_peer_data"].values
    )
    
    sev_counts = out["severity"].value_counts().to_dict()
    logging.info(f"Scoring complete. Severity distribution: {sev_counts}")
    return out
