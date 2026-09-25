import json
import joblib
from pathlib import Path
import pandas as pd
from typing import Dict, Any
from .config import Model3Config

class ArtifactManager:
    def __init__(self, config: Model3Config):
        self.config = config

    def save_scores(self, scored_df: pd.DataFrame):
        self.config.model_output_dir.mkdir(parents=True, exist_ok=True)
        # Select output contract columns
        output_cols = [
            "work_id",
            "house",
            "state",
            "district",
            "ida",
            "mp_name",
            "work_status",
            "sanction_amount",
            "total_disbursed_amount",
            "utilization_ratio",
            "transaction_count",
            "payment_concentration_hhi",
            "days_to_first_disbursement",
            "raw_score",
            "fund_anomaly_score",
            "severity",
            "audit_category",
            "anomaly_reasons",
            "explanation"
        ]
        # Only retain columns that exist
        save_cols = [c for c in output_cols if c in scored_df.columns]
        scored_df[save_cols].to_parquet(self.config.scores_output_path, index=False)

    def save_model(self, model, scaler):
        self.config.model_save_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, self.config.model_joblib_path)
        joblib.dump(scaler, self.config.scaler_joblib_path)

    def save_metadata(self, metadata: Dict[str, Any]):
        self.config.model_save_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config.metadata_json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
