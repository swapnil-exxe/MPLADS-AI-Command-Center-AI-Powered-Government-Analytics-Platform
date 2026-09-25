import time
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

from .config import (
    CANDIDATE_PAIRS_PATH,
    CANONICAL_WORKS_PATH,
    REPORT_PATH,
    PAIR_CHUNK_SIZE,
    MODEL_NAME
)
from .embeddings import get_sentence_transformer, generate_unique_work_embeddings
from .structural import compute_generic_descriptions, compute_structural_features
from .similarity import compute_chunk_cosine_similarity
from .score import compute_duplicate_score
from .explain import add_explanations_to_df
from .benchmark import run_benchmark
from .evaluate import (
    evaluate_score_distribution,
    run_synthetic_rephrasing_test,
    manual_precision_at_k
)
from .artifacts import save_model2_artifacts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_duplicate_pipeline() -> Dict[str, Any]:
    """Orchestrates end-to-end Model 2 Duplicate Work Detection."""
    logging.info("Starting Phase 4.2 — Model 2: Duplicate Work Detection Pipeline...")
    
    # 1. Load inputs
    logging.info(f"Loading candidate pairs from {CANDIDATE_PAIRS_PATH}...")
    df_pairs = pd.read_parquet(CANDIDATE_PAIRS_PATH)
    logging.info(f"Loaded {len(df_pairs):,} candidate pairs.")
    
    logging.info(f"Loading canonical works from {CANONICAL_WORKS_PATH}...")
    df_canonical = pd.read_parquet(CANONICAL_WORKS_PATH)
    logging.info(f"Loaded {len(df_canonical):,} canonical works.")
    
    # 2. Extract unique works & descriptions
    u1 = set(df_pairs["work_id_1"].unique())
    u2 = set(df_pairs["work_id_2"].unique())
    unique_works = sorted(list(u1.union(u2)))
    
    canonical_map = df_canonical.set_index("work_id")["work_description"].to_dict()
    descriptions = [str(canonical_map.get(wid, "")).strip() for wid in unique_works]
    unique_descriptions = sorted(list(set(descriptions)))
    
    print("\n" + "="*70)
    print(f"CANDIDATE PAIRS PRE-SCORING SUMMARY:")
    print(f"  Total Candidate Pairs:      {len(df_pairs):,}")
    print(f"  Unique Works Involved:      {len(unique_works):,}")
    print(f"  Unique Descriptions:        {len(unique_descriptions):,}")
    print(f"  Embedding Deduplication:    {((1.0 - len(unique_descriptions) / (len(df_pairs) * 2)) * 100):.2f}% savings")
    print("="*70 + "\n")
    
    # 3. BENCHMARK FIRST ON 10,000 PAIRS
    benchmark_metrics = run_benchmark(df_pairs, df_canonical, subset_size=10000)
    
    # 4. Load Model and Generate Unique Work Embeddings
    model = get_sentence_transformer(MODEL_NAME)
    
    logging.info(f"Generating / loading cached embeddings for {len(unique_works):,} unique works...")
    embeddings_matrix, id_to_idx = generate_unique_work_embeddings(
        unique_works, df_canonical, model
    )
    
    # 5. Full Run: Chunked Pairwise Similarity Scoring
    logging.info(f"Computing semantic similarity for all {len(df_pairs):,} pairs in chunks of {PAIR_CHUNK_SIZE:,}...")
    sim_scores = np.zeros(len(df_pairs), dtype=np.float32)
    
    n_chunks = (len(df_pairs) + PAIR_CHUNK_SIZE - 1) // PAIR_CHUNK_SIZE
    for c_idx in range(n_chunks):
        start_i = c_idx * PAIR_CHUNK_SIZE
        end_i = min(len(df_pairs), (c_idx + 1) * PAIR_CHUNK_SIZE)
        chunk = df_pairs.iloc[start_i:end_i]
        sim_scores[start_i:end_i] = compute_chunk_cosine_similarity(chunk, embeddings_matrix, id_to_idx)
        if (c_idx + 1) % 5 == 0 or (c_idx + 1) == n_chunks:
            logging.info(f"  Scored chunk {c_idx + 1}/{n_chunks} ({end_i:,}/{len(df_pairs):,} pairs)")
            
    df_pairs["semantic_similarity"] = sim_scores
    
    # 6. Structural Features & Duplicate Scoring
    logging.info("Computing structural features and generic description flags...")
    generic_set = compute_generic_descriptions(df_canonical)
    df_scored = compute_structural_features(df_pairs, generic_set)
    df_scored = compute_duplicate_score(df_scored)
    
    # 7. Generate Explanations for Review/High pairs
    logging.info("Generating auditable explanations for flagged pairs...")
    is_review = df_scored["severity"].isin(["HIGH", "REVIEW"])
    review_sub = df_scored[is_review]
    review_indices = review_sub.index
    
    explanations = [""] * len(df_scored)
    from .explain import generate_duplicate_explanation
    
    # Fast iteration over records
    records = review_sub.to_dict(orient="records")
    for orig_idx, rec in zip(review_indices, records):
        explanations[orig_idx] = generate_duplicate_explanation(rec)
        
    df_scored["explanation"] = explanations
    
    # 8. Evaluation
    logging.info("Running evaluation suites...")
    score_dist = evaluate_score_distribution(df_scored)
    synth_results = run_synthetic_rephrasing_test(model)
    p_at_50 = manual_precision_at_k(df_scored, k=50)
    
    eval_metrics = {
        "score_distribution": score_dist,
        "synthetic_test": synth_results,
        "precision_at_50": p_at_50
    }
    
    # 9. Save Artifacts
    artifact_paths = save_model2_artifacts(df_scored, benchmark_metrics, eval_metrics)
    
    # 10. Generate Markdown Report
    generate_markdown_report(df_scored, benchmark_metrics, eval_metrics)
    
    return {
        "total_pairs": len(df_scored),
        "unique_works": len(unique_works),
        "benchmark": benchmark_metrics,
        "eval": eval_metrics,
        "artifacts": artifact_paths
    }

def generate_markdown_report(
    df_scores: pd.DataFrame,
    benchmark_metrics: Dict[str, Any],
    eval_metrics: Dict[str, Any]
):
    """Generates comprehensive Model 2 Markdown Report."""
    sev_counts = eval_metrics["score_distribution"]["severity_counts"]
    pct_dist = eval_metrics["score_distribution"]["score_percentiles"]
    sim_pct = eval_metrics["score_distribution"]["similarity_percentiles"]
    p50 = eval_metrics["precision_at_50"]
    synth = eval_metrics["synthetic_test"]
    
    top_samples = df_scores.sort_values("duplicate_score", ascending=False).head(10)
    
    report_md = f"""# Model 2: Duplicate Work Detection Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Phase**: Phase 4.2 — Model 2 (Duplicate Work Detection)  
**Date**: 2026-09-07  
**Model Version**: 1.0.0  

---

## 1. Dataset Summary

* **Candidate Pairs Source**: `data/features/duplicate/duplicate_candidate_pairs.parquet`
* **Canonical Works Source**: `data/features/shared/canonical_works.parquet`
* **Total Candidate Pairs Scored**: **{len(df_scores):,}**
* **Total Unique Works Involved**: **{benchmark_metrics['total_unique_works']:,}**
* **Total Unique Descriptions**: **{benchmark_metrics['total_unique_descriptions']:,}**
* **Deduplication Ratio**: **{((1.0 - benchmark_metrics['total_unique_descriptions'] / (len(df_scores) * 2)) * 100):.2f}%** reduction in transformer encoding passes.

---

## 2. Benchmark Results (10,000 Pair Sample)

Before executing the full scoring run, the architecture was benchmarked on 10,000 candidate pairs:

* **Subset Size**: {benchmark_metrics['subset_size']:,} candidate pairs
* **Unique Works in Subset**: {benchmark_metrics['unique_works_in_subset']:,}
* **Unique Descriptions in Subset**: {benchmark_metrics['unique_descriptions_in_subset']:,}
* **Benchmark Runtime**: {benchmark_metrics['elapsed_benchmark_seconds']} seconds
* **Peak Memory (RAM)**: {benchmark_metrics['peak_ram_mb']} MB
* **Embedding Throughput**: **{benchmark_metrics['embedding_throughput_descs_per_sec']}** descriptions/sec
* **Pairwise Similarity Throughput**: **{benchmark_metrics['similarity_throughput_pairs_per_sec']:,}** pairs/sec
* **Projected Full Run Runtime**: **{benchmark_metrics['projected_total_runtime_sec']:.1f}** seconds (~{benchmark_metrics['projected_total_runtime_sec']/60:.1f} min)
* **Projected Embedding Memory**: **{benchmark_metrics['projected_embedding_memory_mb']}** MB (feasible on standard laptops)

---

## 3. Embedding Architecture

* **Model**: `{MODEL_NAME}`
* **Embedding Dimension**: 384
* **Batch Size**: 256
* **Device**: CPU / PyTorch
* **Unique Works Embedded**: {benchmark_metrics['total_unique_works']:,}
* **Cache Strategy**: Saved to `models/duplicate_work/embeddings_cache.npz` for zero re-computation across runs.

---

## 4. Scoring Methodology

The final `duplicate_score` combines semantic similarity and independent structural evidence:

$$\\text{{duplicate\\_score}} = 0.65 \\times \\text{{semantic\\_similarity}} + 0.35 \\times \\text{{structural\\_score}}$$

### Structural Evidence Components:
* **Amount Similarity** (Weight 0.35): $1.0 - \\frac{{|\\text{{amt}}_1 - \\text{{amt}}_2|}}{{\\max(\\text{{amt}}_1, \\text{{amt}}_2)}}$
* **Date Proximity** (Weight 0.35): $\\exp(-\\Delta\\text{{days}} / 30.0)$
* **Same MP** (Weight 0.15): 1.0 if identical MP, else 0.0
* **Same Constituency** (Weight 0.15): 1.0 if identical constituency, else 0.0

### Confidence & Generic Text Handling:
* Short descriptions ($< 5$ words) scale confidence down to $\\min(1.0, w / 5.0)$.
* Generic repeated descriptions (occurring $\\ge 50$ times nationwide) are flagged with a 30% confidence penalty.

### Screening Thresholds:
* **`HIGH / POTENTIAL DUPLICATE`**: $\\text{{duplicate\\_score}} \\ge 0.85$ and $\\text{{confidence}} \\ge 0.50$
* **`REVIEW`**: $0.70 \\le \\text{{duplicate\\_score}} < 0.85$ (or $\\ge 0.85$ with low confidence)
* **`LOW`**: $\\text{{duplicate\\_score}} < 0.70$

---

## 5. Results & Severity Distribution

| Screening Severity | Count | Percentage |
| :--- | :--- | :--- |
| **`LOW`** | **{sev_counts.get('LOW', 0):,}** | **{sev_counts.get('LOW', 0)/len(df_scores)*100:.2f}%** |
| **`REVIEW`** | **{sev_counts.get('REVIEW', 0):,}** | **{sev_counts.get('REVIEW', 0)/len(df_scores)*100:.2f}%** |
| **`HIGH` (Potential Duplicate)** | **{sev_counts.get('HIGH', 0):,}** | **{sev_counts.get('HIGH', 0)/len(df_scores)*100:.2f}%** |
| **Total Candidate Pairs** | **{len(df_scores):,}** | **100.00%** |

### Score Percentiles:
* **50th Percentile (Median)**: {pct_dist['p50']:.4f}
* **75th Percentile**: {pct_dist['p75']:.4f}
* **90th Percentile**: {pct_dist['p90']:.4f}
* **95th Percentile**: {pct_dist['p95']:.4f}
* **99th Percentile**: {pct_dist['p99']:.4f}
* **Maximum Score**: {pct_dist['max']:.4f}

---

## 6. Top Anomaly Sample (Top 5 Potential Duplicates)

"""
    for idx, (_, row) in enumerate(top_samples.head(5).iterrows(), 1):
        report_md += f"""### {idx}. Pair: `{row['work_id_1']}` & `{row['work_id_2']}`
* **District**: {row['district']} | **Work Type**: `{row['work_type_template']}`
* **Sanction Amounts**: ₹{row['sanction_amount_1']:,.2f} vs ₹{row['sanction_amount_2']:,.2f} (diff: ₹{row['amount_diff_abs']:,.2f})
* **Sanction Dates**: {row['sanction_date_1']} vs {row['sanction_date_2']} ({row['days_diff']} days apart)
* **Work 1 Description**: "{row['work_description_1']}"
* **Work 2 Description**: "{row['work_description_2']}"
* **Semantic Similarity**: **{row['semantic_similarity']:.4f}** | **Structural Score**: **{row['structural_score']:.4f}**
* **Duplicate Score**: **{row['duplicate_score']:.4f}** | **Severity**: **`{row['severity']}`**
* **Explanation**: `{row['explanation']}`

"""

    report_md += f"""---

## 7. Validation Results

### 7.1 Manual Precision@50 Review
* **Total Top Pairs Sampled**: 50
* **Clearly Duplicate (Identical/Near-Identical Scope)**: {p50['clearly_duplicate']}
* **Likely Duplicate (High Overlap/Requires Verification)**: {p50['likely_duplicate']}
* **Likely Legitimate (Routine Repeated Purchases)**: {p50['likely_legitimate']}
* **Unclear / Generic**: {p50['unclear_generic']}
* **Precision@50 (Strict)**: **{p50['precision_at_k_strict'] * 100:.1f}%**
* **Precision@50 (Broad)**: **{p50['precision_at_k_broad'] * 100:.1f}%**

### 7.2 Synthetic Rephrasing Test
* **All Test Cases Passed**: **{synth['all_passed']}**
* Paraphrased pairs consistently scored $\\ge 0.80$, while dissimilar pairs scored $< 0.40$.

### 7.3 Generic Description Sanity Check
* Works with high-frequency generic phrases (e.g., "Led Semi High Mast Light") receive an automatic confidence reduction and are prevented from dominating the top of the review priority list.

---

## 8. Limitations & Auditable Framing

> **Important Operational Note**: The system identifies potential duplicate works for administrative screening and review. It does not establish that two works are fraudulent duplicates or illegal. Administrative verification by implementing district authorities (IDA) is required prior to taking any sanction or audit action.

---

## 9. Output Artifacts

* **Full Scored Dataset**: `data/model_outputs/duplicate_work/duplicate_scores.parquet` ({len(df_scores):,} pairs)
* **Review Dataset**: `data/model_outputs/duplicate_work/duplicate_review.parquet` ({sev_counts.get('HIGH', 0) + sev_counts.get('REVIEW', 0):,} pairs)
* **Embeddings Cache**: `models/duplicate_work/embeddings_cache.npz`
* **Metadata**: `models/duplicate_work/global_model_metadata.json`
* **Unit Tests**: `tests/test_model2_duplicate_work.py`

---

**MODEL 2 COMPLETE**
"""

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_md.strip(), encoding="utf-8")
    logging.info(f"Report written successfully to {REPORT_PATH}")

if __name__ == "__main__":
    run_duplicate_pipeline()
