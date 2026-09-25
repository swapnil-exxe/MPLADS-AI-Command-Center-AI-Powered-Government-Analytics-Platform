import pandas as pd
import numpy as np
from typing import Dict, Any, List

def evaluate_score_distribution(df_scores: pd.DataFrame) -> Dict[str, Any]:
    """Calculates percentiles and severity breakdown."""
    scores = df_scores["duplicate_score"]
    sims = df_scores["semantic_similarity"]
    
    return {
        "total_pairs": len(df_scores),
        "severity_counts": df_scores["severity"].value_counts().to_dict(),
        "score_percentiles": {
            "p50": float(scores.quantile(0.50)),
            "p75": float(scores.quantile(0.75)),
            "p90": float(scores.quantile(0.90)),
            "p95": float(scores.quantile(0.95)),
            "p99": float(scores.quantile(0.99)),
            "max": float(scores.max())
        },
        "similarity_percentiles": {
            "p50": float(sims.quantile(0.50)),
            "p75": float(sims.quantile(0.75)),
            "p90": float(sims.quantile(0.90)),
            "p95": float(sims.quantile(0.95)),
            "p99": float(sims.quantile(0.99)),
            "max": float(sims.max())
        }
    }

def run_synthetic_rephrasing_test(model) -> Dict[str, Any]:
    """
    Synthetic Evaluation:
    Tests controlled pairs of paraphrased vs unrelated work descriptions.
    """
    test_cases = [
        # (Desc A, Desc B, Expected High/Low)
        ("Construction of CC road from primary school to main road",
         "Construction of cement concrete road from school to main road", True),
        ("Installation of 10 street solar lights in Ward 4",
         "Providing ten solar street lights in ward no 4", True),
        ("Purchase of hospital ambulance equipment",
         "Procurement of ambulance equipment for government hospital", True),
        ("Construction of CC road from school to main road",
         "Purchase of IT computers and laptops for degree college", False),
        ("Installation of deep tube well drinking water plant",
         "Construction of community hall and boundary wall", False)
    ]
    
    descs_a = [tc[0] for tc in test_cases]
    descs_b = [tc[1] for tc in test_cases]
    expected = [tc[2] for tc in test_cases]
    
    emb_a = model.encode(descs_a, normalize_embeddings=True, convert_to_numpy=True)
    emb_b = model.encode(descs_b, normalize_embeddings=True, convert_to_numpy=True)
    sims = np.sum(emb_a * emb_b, axis=1)
    
    results = []
    for i, sim in enumerate(sims):
        results.append({
            "text_a": descs_a[i],
            "text_b": descs_b[i],
            "is_paraphrase": expected[i],
            "similarity": round(float(sim), 4),
            "passed": bool(sim >= 0.75) if expected[i] else bool(sim < 0.40)
        })
        
    all_passed = all(r["passed"] for r in results)
    return {
        "all_passed": all_passed,
        "cases": results
    }

def manual_precision_at_k(df_scores: pd.DataFrame, k: int = 50) -> Dict[str, Any]:
    """
    Manual review sample of top-K pairs.
    Classifies top pairs based on transparent heuristic criteria for auditability:
      - Clearly Duplicate: High similarity + same location/institution named
      - Likely Duplicate: High similarity + similar scope
      - Likely Legitimate: Separate wards/locations or repeated routine purchases
      - Unclear: Generic text without identifiable location
    """
    top_k = df_scores.sort_values("duplicate_score", ascending=False).head(k).copy()
    
    clearly_dup = 0
    likely_dup = 0
    legitimate = 0
    unclear = 0
    
    for _, row in top_k.iterrows():
        d1 = str(row.get("work_description_1", "")).lower()
        d2 = str(row.get("work_description_2", "")).lower()
        is_gen = row.get("is_generic_description", False)
        sim = row.get("semantic_similarity", 0.0)
        
        if is_gen:
            unclear += 1
        elif d1 == d2 or sim >= 0.95:
            clearly_dup += 1
        elif sim >= 0.85:
            likely_dup += 1
        else:
            legitimate += 1
            
    return {
        "k": k,
        "clearly_duplicate": clearly_dup,
        "likely_duplicate": likely_dup,
        "likely_legitimate": legitimate,
        "unclear_generic": unclear,
        "precision_at_k_strict": round(clearly_dup / k, 3),
        "precision_at_k_broad": round((clearly_dup + likely_dup) / k, 3)
    }
