import json
from pathlib import Path
import pandas as pd
from typing import Dict, Any
from .config import (
    SCORES_OUTPUT_PATH,
    REVIEW_OUTPUT_PATH,
    METADATA_PATH,
    MODEL_NAME,
    EMBEDDING_DIM,
    WEIGHT_SEMANTIC,
    WEIGHT_STRUCTURAL,
    THRESHOLD_HIGH,
    THRESHOLD_REVIEW
)

def save_model2_artifacts(
    df_scores: pd.DataFrame,
    benchmark_metrics: Dict[str, Any],
    eval_metrics: Dict[str, Any]
) -> Dict[str, str]:
    """Saves duplicate_scores.parquet, duplicate_review.parquet, and metadata JSON."""
    SCORES_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Full scores
    print(f"Saving full duplicate scores ({len(df_scores):,} pairs) to {SCORES_OUTPUT_PATH}...")
    df_scores.to_parquet(SCORES_OUTPUT_PATH, index=False)
    
    # 2. Review subset (severity in ['HIGH', 'REVIEW'])
    df_review = df_scores[df_scores["severity"].isin(["HIGH", "REVIEW"])].copy()
    print(f"Saving review subset ({len(df_review):,} pairs) to {REVIEW_OUTPUT_PATH}...")
    df_review.to_parquet(REVIEW_OUTPUT_PATH, index=False)
    
    # 3. Metadata
    metadata = {
        "model_version": "1.0.0",
        "embedding_model": MODEL_NAME,
        "embedding_dim": EMBEDDING_DIM,
        "weights": {
            "semantic_similarity": WEIGHT_SEMANTIC,
            "structural_score": WEIGHT_STRUCTURAL
        },
        "thresholds": {
            "high": THRESHOLD_HIGH,
            "review": THRESHOLD_REVIEW
        },
        "total_pairs_scored": len(df_scores),
        "review_pairs_count": len(df_review),
        "benchmark_metrics": benchmark_metrics,
        "evaluation_summary": {
            "severity_distribution": eval_metrics.get("score_distribution", {}).get("severity_counts", {}),
            "precision_at_50": eval_metrics.get("precision_at_50", {}),
            "synthetic_test_passed": eval_metrics.get("synthetic_test", {}).get("all_passed", False)
        }
    }
    
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved global model metadata to {METADATA_PATH}")
    
    return {
        "scores_path": str(SCORES_OUTPUT_PATH),
        "review_path": str(REVIEW_OUTPUT_PATH),
        "metadata_path": str(METADATA_PATH)
    }
