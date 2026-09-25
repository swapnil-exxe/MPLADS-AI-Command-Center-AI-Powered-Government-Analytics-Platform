import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from typing import Tuple, Dict, Any
from .config import Model3Config

class FeatureEngineer:
    def __init__(self, config: Model3Config):
        self.config = config
        self.scaler = RobustScaler()

    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
        """
        Processes raw expenditure feature dataset:
        1. Segregates into active cohort (>0 disbursed) and zero-spend cohort.
        2. Computes the 6 non-redundant transformed features.
        3. Scales active features using RobustScaler.
        4. Identifies deterministic zero-spend categories.
        """
        df = df.copy()
        if "sanction_date" in df.columns:
            df["sanction_date"] = pd.to_datetime(df["sanction_date"], errors="coerce")

        # Segregate cohorts
        is_active = (df["total_disbursed_amount"] > 0)
        df_active = df[is_active].copy()
        df_zero = df[~is_active].copy()

        if "vendor_count" in df.columns:
            df_active["vendor_count"] = df_active["vendor_count"].fillna(1.0).astype(float)
            df_zero["vendor_count"] = 0.0
        else:
            df_active["vendor_count"] = 1.0
            df_zero["vendor_count"] = 0.0

        # Feature transformations for active cohort
        df_active["log_disbursed_amount"] = np.log1p(df_active["total_disbursed_amount"].astype(float))
        df_active["transaction_count_log"] = np.log1p(df_active["transaction_count"].astype(float))
        df_active["days_to_first_disbursement_log"] = np.log1p(
            np.maximum(0.0, df_active["days_to_first_disbursement"].fillna(0.0).astype(float))
        )
        df_active["spending_window_days_log"] = np.log1p(
            np.maximum(0.0, df_active["spending_window_days"].fillna(0.0).astype(float))
        )
        # Bounded features
        df_active["utilization_ratio"] = df_active["utilization_ratio"].clip(0.0, 1.0).astype(float)
        df_active["payment_concentration_hhi"] = df_active["payment_concentration_hhi"].clip(0.0, 1.0).astype(float)

        X_active = df_active[self.config.core_features].values
        X_scaled = self.scaler.fit_transform(X_active)

        # Zero-spend cohort deterministic classification
        # Reference date for project age: latest sanction date in dataset or current time
        ref_date = df["sanction_date"].max() if not df["sanction_date"].isna().all() else pd.Timestamp.now()
        days_since_sanction = (ref_date - df_zero["sanction_date"]).dt.days.fillna(0)
        df_zero["sanction_age_days"] = days_since_sanction

        late_statuses = {"Work Completed", "Physical Inspection", "Work partially Completed"}
        is_status_mismatch = df_zero["work_status"].isin(late_statuses)
        is_dormant = (~is_status_mismatch) & (days_since_sanction > self.config.dormant_sanction_days_threshold)

        df_zero["zero_spend_category"] = np.where(
            is_status_mismatch,
            "STATUS_EXPENDITURE_MISMATCH",
            np.where(is_dormant, "DORMANT_SANCTION", "NORMAL_AWAITING_DISBURSEMENT")
        )

        return df, df_active, df_zero, X_scaled

    def transform_active(self, df_active: pd.DataFrame) -> np.ndarray:
        """Transforms active works using pre-fitted scaler."""
        df_active = df_active.copy()
        df_active["log_disbursed_amount"] = np.log1p(df_active["total_disbursed_amount"].astype(float))
        df_active["transaction_count_log"] = np.log1p(df_active["transaction_count"].astype(float))
        df_active["days_to_first_disbursement_log"] = np.log1p(
            np.maximum(0.0, df_active["days_to_first_disbursement"].fillna(0.0).astype(float))
        )
        df_active["spending_window_days_log"] = np.log1p(
            np.maximum(0.0, df_active["spending_window_days"].fillna(0.0).astype(float))
        )
        df_active["utilization_ratio"] = df_active["utilization_ratio"].clip(0.0, 1.0).astype(float)
        df_active["payment_concentration_hhi"] = df_active["payment_concentration_hhi"].clip(0.0, 1.0).astype(float)
        X_active = df_active[self.config.core_features].values
        return self.scaler.transform(X_active)
