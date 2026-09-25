import joblib
from pathlib import Path
import numpy as np
from sklearn.ensemble import IsolationForest
from .config import Model3Config

class FundIsolationForest:
    def __init__(self, config: Model3Config):
        self.config = config
        self.model = IsolationForest(
            n_estimators=config.n_estimators,
            contamination=config.contamination,
            max_samples=config.max_samples,
            random_state=config.random_state,
            n_jobs=config.n_jobs
        )

    def fit(self, X: np.ndarray) -> "FundIsolationForest":
        self.model.fit(X)
        return self

    def raw_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """
        Computes raw anomaly scores where higher values mean more anomalous.
        In scikit-learn, decision_function returns positive for inliers, negative for outliers.
        Therefore: s_raw = -decision_function(X).
        """
        return -self.model.decision_function(X)

    def save(self, model_path: Path):
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, model_path)

    @classmethod
    def load(cls, model_path: Path, config: Model3Config) -> "FundIsolationForest":
        instance = cls(config)
        instance.model = joblib.load(model_path)
        return instance
