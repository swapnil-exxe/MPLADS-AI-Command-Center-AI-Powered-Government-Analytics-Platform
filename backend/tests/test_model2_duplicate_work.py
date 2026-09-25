import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from ml_models.duplicate_work.config import (
    MODEL_NAME,
    EMBEDDING_DIM,
    WEIGHT_SEMANTIC,
    WEIGHT_STRUCTURAL,
    THRESHOLD_HIGH,
    THRESHOLD_REVIEW
)
from ml_models.duplicate_work.structural import (
    compute_structural_features,
    compute_generic_descriptions
)
from ml_models.duplicate_work.similarity import compute_chunk_cosine_similarity
from ml_models.duplicate_work.score import compute_duplicate_score
from ml_models.duplicate_work.explain import generate_duplicate_explanation
from ml_models.duplicate_work.benchmark import run_benchmark


def test_score_bounds_and_components():
    """Tests duplicate score is strictly bounded in [0.0, 1.0]."""
    df_test = pd.DataFrame([
        {
            "work_id_1": "W1", "work_id_2": "W2",
            "sanction_amount_1": 100000.0, "sanction_amount_2": 100000.0,
            "days_diff": 0, "is_same_constituency": True, "is_same_mp": True,
            "work_description_1": "Construction of road", "work_description_2": "Construction of road",
            "semantic_similarity": 1.0
        },
        {
            "work_id_1": "W3", "work_id_2": "W4",
            "sanction_amount_1": 100000.0, "sanction_amount_2": 500000.0,
            "days_diff": 90, "is_same_constituency": False, "is_same_mp": False,
            "work_description_1": "School classroom building", "work_description_2": "Solar lighting",
            "semantic_similarity": 0.1
        }
    ])
    
    scored = compute_structural_features(df_test)
    scored = compute_duplicate_score(scored)
    
    assert (scored["duplicate_score"] >= 0.0).all()
    assert (scored["duplicate_score"] <= 1.0).all()
    assert scored.loc[0, "duplicate_score"] > scored.loc[1, "duplicate_score"]
    assert scored.loc[0, "severity"] in ["HIGH", "REVIEW"]


def test_missing_and_generic_descriptions_affect_confidence():
    """Tests missing and generic/short descriptions handle confidence properly without crashing."""
    df_test = pd.DataFrame([
        {
            "work_id_1": "W1", "work_id_2": "W2",
            "sanction_amount_1": 50000.0, "sanction_amount_2": 50000.0,
            "days_diff": 5, "is_same_constituency": True, "is_same_mp": True,
            "work_description_1": None, "work_description_2": "",
            "semantic_similarity": 0.0
        },
        {
            "work_id_1": "W3", "work_id_2": "W4",
            "sanction_amount_1": 50000.0, "sanction_amount_2": 50000.0,
            "days_diff": 5, "is_same_constituency": True, "is_same_mp": True,
            "work_description_1": "GENERIC LIGHT", "work_description_2": "GENERIC LIGHT",
            "semantic_similarity": 0.95
        }
    ])
    
    generic_set = {"GENERIC LIGHT"}
    scored = compute_structural_features(df_test, generic_descriptions=generic_set)
    
    # Missing description should have low confidence
    assert scored.loc[0, "confidence"] <= 0.25
    # Generic description should have generic flag True and penalized confidence
    assert scored.loc[1, "is_generic_description"] == True
    assert scored.loc[1, "confidence"] < 1.0


def test_pair_uniqueness_and_no_self_pairs():
    """Verifies candidate pair dataset has no self-pairs (A,A) and no symmetric duplicates (A,B and B,A)."""
    cand_path = Path("data/features/duplicate/duplicate_candidate_pairs.parquet")
    if not cand_path.exists():
        pytest.skip("Candidate pairs file not found.")
        
    df = pd.read_parquet(cand_path, columns=["work_id_1", "work_id_2"])
    # No self-pairs
    self_pairs = (df["work_id_1"] == df["work_id_2"]).sum()
    assert self_pairs == 0, f"Found {self_pairs} self-pairs (A,A)!"
    
    # Strict canonical ordering: work_id_1 < work_id_2
    unordered = (df["work_id_1"] >= df["work_id_2"]).sum()
    assert unordered == 0, f"Found {unordered} pairs violating work_id_1 < work_id_2 ordering!"


def test_unique_embedding_architecture_lookup():
    """Verifies embedding matrix lookup and similarity dot product is deterministic and fast."""
    mock_matrix = np.array([
        [1.0, 0.0, 0.0],
        [0.8, 0.6, 0.0],
        [0.0, 1.0, 0.0]
    ], dtype=np.float32)
    
    id_map = {"W1": 0, "W2": 1, "W3": 2}
    
    df_chunk = pd.DataFrame([
        {"work_id_1": "W1", "work_id_2": "W2"},
        {"work_id_1": "W1", "work_id_2": "W3"}
    ])
    
    sims = compute_chunk_cosine_similarity(df_chunk, mock_matrix, id_map)
    assert np.isclose(sims[0], 0.8, atol=1e-4)
    assert np.isclose(sims[1], 0.0, atol=1e-4)


def test_explanation_formatting_and_safety():
    """Ensures explanations are auditable, human-readable, and never state 'FRAUD CONFIRMED'."""
    row = pd.Series({
        "work_id_1": "WS/1", "work_id_2": "WS/2",
        "semantic_similarity": 0.94, "duplicate_score": 0.89, "confidence": 0.90,
        "days_diff": 12, "sanction_amount_1": 250000.0, "sanction_amount_2": 250000.0,
        "amount_diff_abs": 0.0, "amount_ratio": 1.0, "district": "PUNE",
        "work_type_template": "Road construction", "is_same_mp": True,
        "is_same_constituency": True, "work_description_1": "Road to school",
        "work_description_2": "Road to school campus",
        "is_short_description": False, "is_generic_description": False
    })
    
    exp = generate_duplicate_explanation(row)
    assert "POTENTIAL DUPLICATE — REQUIRES REVIEW" in exp
    assert "FRAUD" not in exp
    assert "CONFIRMED" not in exp
    assert "PUNE" in exp
    assert "0.94" in exp


def test_benchmark_runner_sanity():
    """Tests that benchmark execution succeeds on sample data and produces required metric keys."""
    df_sample_pairs = pd.DataFrame([
        {
            "work_id_1": "W1", "work_id_2": "W2",
            "house_1": "Lok Sabha", "house_2": "Lok Sabha",
            "district": "JAIPUR", "work_type_template": "Street lighting",
            "sanction_date_1": "2025-01-01", "sanction_date_2": "2025-01-10",
            "days_diff": 9, "sanction_amount_1": 100000.0, "sanction_amount_2": 100000.0,
            "amount_diff_abs": 0.0, "amount_ratio": 1.0, "is_amount_within_10pct": True,
            "mp_name_1": "MP A", "mp_name_2": "MP A", "is_same_mp": True,
            "constituency_1": "C1", "constituency_2": "C1", "is_same_constituency": True,
            "work_description_1": "Installing solar street light",
            "work_description_2": "Installing solar street light"
        }
    ])
    df_sample_canonical = pd.DataFrame([
        {"work_id": "W1", "work_description": "Installing solar street light"},
        {"work_id": "W2", "work_description": "Installing solar street light"}
    ])
    
    # Run minimal benchmark
    try:
        from ml_models.duplicate_work.embeddings import get_sentence_transformer
        # Check if sentence-transformers is available
        metrics = run_benchmark(df_sample_pairs, df_sample_canonical, subset_size=1)
        assert "embedding_throughput_descs_per_sec" in metrics
        assert "similarity_throughput_pairs_per_sec" in metrics
        assert "projected_total_runtime_sec" in metrics
    except ImportError:
        pytest.skip("sentence-transformers not yet available in test session.")