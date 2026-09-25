import json
import logging
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any
import joblib

from .config import (
    MODEL_OUTPUTS_DIR,
    OUTPUT_PARQUET_PATH,
    MODELS_DIR,
    PEER_MODELS_DIR,
    MODEL_VERSION,
    N_ESTIMATORS,
    CONTAMINATION,
    MAX_SAMPLES,
    RANDOM_STATE,
    MODEL_FEATURE_COLS,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def compute_feature_schema_hash(feature_cols: list) -> str:
    """Computes SHA256 hash of the feature schema column names for reproducibility."""
    schema_str = ",".join(sorted(feature_cols))
    return hashlib.sha256(schema_str.encode("utf-8")).hexdigest()[:16]

def save_model_artifacts(
    peer_models: Dict[str, Dict[str, Any]],
    total_training_works: int,
    output_dir: Path = MODELS_DIR
) -> Path:
    """
    Saves trained peer Isolation Forest models and metadata to models/cost_anomaly/.
    """
    logging.info(f"Saving model artifacts to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    peer_dir = output_dir / "peer_models"
    peer_dir.mkdir(parents=True, exist_ok=True)
    
    saved_models_meta = []
    
    for grp_name, info in peer_models.items():
        # Sanitize group name for filename
        sanitized_name = "".join([c if c.isalnum() else "_" for c in grp_name])
        model_filename = f"{sanitized_name}.joblib"
        model_path = peer_dir / model_filename
        
        # Save model joblib
        joblib.dump(info["model"], model_path)
        
        saved_models_meta.append({
            "peer_group_name": grp_name,
            "peer_group_level": info["peer_group_level"],
            "peer_group_size": info["peer_group_size"],
            "peer_median_amount": info["peer_median_amount"],
            "peer_iqr_amount": info["peer_iqr_amount"],
            "model_file": model_filename
        })
        
    global_meta = {
        "model_version": MODEL_VERSION,
        "trained_at": pd.Timestamp.now().isoformat(),
        "total_training_works": total_training_works,
        "peer_group_count": len(peer_models),
        "hyperparameters": {
            "n_estimators": N_ESTIMATORS,
            "contamination": CONTAMINATION,
            "max_samples": MAX_SAMPLES,
            "random_state": RANDOM_STATE
        },
        "feature_schema": MODEL_FEATURE_COLS,
        "feature_schema_hash": compute_feature_schema_hash(MODEL_FEATURE_COLS),
        "peer_models_summary": saved_models_meta
    }
    
    meta_json_path = output_dir / "global_model_metadata.json"
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(global_meta, f, indent=2, default=str)
        
    logging.info(f"Saved global model metadata to {meta_json_path} and {len(saved_models_meta):,} peer models to {peer_dir}.")
    return meta_json_path

def save_scored_output_parquet(
    df_scored: pd.DataFrame,
    output_path: Path = OUTPUT_PARQUET_PATH
) -> Path:
    """
    Saves Model 1 scored output dataset as Parquet for downstream consumption.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cols_to_save = [
        "work_id", "house", "state", "district", "ida", "mp_name", "constituency_or_term",
        "work_category", "work_type_template", "sanction_amount", "sanction_amount_log",
        "peer_group_used", "peer_group_level", "peer_group_size", "is_data_quality_exception",
        "raw_anomaly_score", "cost_anomaly_score", "severity", "explanation"
    ]
    cols_present = [c for c in cols_to_save if c in df_scored.columns]
    
    df_out = df_scored[cols_present].copy()
    df_out.to_parquet(output_path, index=False)
    
    logging.info(f"Exported Model 1 scored dataset ({len(df_out):,} rows) to {output_path}")
    return output_path
