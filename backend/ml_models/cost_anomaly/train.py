import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.ensemble import IsolationForest

from .config import (
    PEER_MIN_GROUP_SIZE,
    RANDOM_STATE,
    N_ESTIMATORS,
    CONTAMINATION,
    MAX_SAMPLES,
    MODEL_FEATURE_COLS,
)
from .preprocessing import prepare_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def train_peer_isolation_forests(
    df_annotated: pd.DataFrame
) -> Dict[str, Dict[str, Any]]:
    """
    Trains one Isolation Forest per valid peer group (size >= PEER_MIN_GROUP_SIZE).
    Excludes sub-1,000 INR data quality exceptions from model fitting.
    
    Returns dictionary mapping peer_group_name -> model dictionary metadata.
    """
    logging.info("Training Isolation Forest models across valid peer groups...")
    
    # Filter out data quality exceptions for clean model fitting
    clean_df = df_annotated[~df_annotated["is_data_quality_exception"]].copy()
    
    peer_models = {}
    grouped = clean_df.groupby("peer_group_used")
    
    trained_count = 0
    skipped_count = 0
    
    for group_name, group_data in grouped:
        group_size = len(group_data)
        if group_size < PEER_MIN_GROUP_SIZE:
            skipped_count += 1
            continue
            
        X_group = prepare_features(group_data)
        
        # Fit Isolation Forest (n_jobs=1 avoids thread pool recreation overhead inside loop)
        clf = IsolationForest(
            n_estimators=N_ESTIMATORS,
            contamination=CONTAMINATION,
            max_samples=MAX_SAMPLES,
            random_state=RANDOM_STATE,
            n_jobs=1
        )
        clf.fit(X_group)
        
        # Compute baseline peer stats for explainability
        sanc_series = group_data["sanction_amount"].fillna(0.0)
        med_amt = float(sanc_series.median())
        q25 = float(sanc_series.quantile(0.25))
        q75 = float(sanc_series.quantile(0.75))
        iqr_amt = float(max(100.0, q75 - q25))
        
        peer_models[group_name] = {
            "model": clf,
            "peer_group_name": group_name,
            "peer_group_level": group_data["peer_group_level"].iloc[0],
            "peer_group_size": group_size,
            "feature_cols": MODEL_FEATURE_COLS,
            "peer_median_amount": med_amt,
            "peer_iqr_amount": iqr_amt,
        }
        trained_count += 1
        
    logging.info(f"Trained {trained_count:,} Isolation Forest peer models. Skipped {skipped_count:,} groups under size N={PEER_MIN_GROUP_SIZE}.")
    return peer_models
