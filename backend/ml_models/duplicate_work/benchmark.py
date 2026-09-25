import time
import tracemalloc
import numpy as np
import pandas as pd
from typing import Dict, Any
from .config import MODEL_NAME, EMBEDDING_DIM, EMBEDDING_BATCH_SIZE
from .embeddings import get_sentence_transformer
from .structural import compute_generic_descriptions, compute_structural_features
from .similarity import compute_chunk_cosine_similarity
from .score import compute_duplicate_score

def run_benchmark(
    df_pairs: pd.DataFrame,
    df_canonical: pd.DataFrame,
    subset_size: int = 10000
) -> Dict[str, Any]:
    """
    Benchmarks Model 2 on a representative subset to verify feasibility before full run.
    Measures:
      - Runtime
      - Peak RAM
      - Unique works involved
      - Unique descriptions
      - Embedding throughput (descriptions/sec)
      - Pairwise similarity throughput (pairs/sec)
      - Full-run projection
    """
    print(f"=== BENCHMARKING ON {subset_size:,} CANDIDATE PAIRS ===")
    sample_pairs = df_pairs.head(subset_size).copy()
    
    # 1. Unique works extraction
    u1 = set(sample_pairs["work_id_1"].unique())
    u2 = set(sample_pairs["work_id_2"].unique())
    unique_works = sorted(list(u1.union(u2)))
    
    canonical_map = df_canonical.set_index("work_id")["work_description"].to_dict()
    descriptions = [str(canonical_map.get(wid, "")).strip() for wid in unique_works]
    unique_descriptions = list(set(descriptions))
    
    tracemalloc.start()
    t0 = time.perf_counter()
    
    # 2. Load model
    t_model_start = time.perf_counter()
    model = get_sentence_transformer(MODEL_NAME)
    t_model = time.perf_counter() - t_model_start
    
    # 3. Benchmark unique description encoding
    t_embed_start = time.perf_counter()
    desc_embeddings = model.encode(
        unique_descriptions,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True
    ).astype(np.float32)
    t_embed = time.perf_counter() - t_embed_start
    embed_throughput = len(unique_descriptions) / max(0.001, t_embed)
    
    # Map back to works
    desc_to_emb = {d: desc_embeddings[i] for i, d in enumerate(unique_descriptions)}
    matrix = np.zeros((len(unique_works), EMBEDDING_DIM), dtype=np.float32)
    id_to_idx = {wid: i for i, wid in enumerate(unique_works)}
    for wid in unique_works:
        matrix[id_to_idx[wid]] = desc_to_emb.get(str(canonical_map.get(wid, "")).strip(), np.zeros(EMBEDDING_DIM, dtype=np.float32))
        
    # 4. Benchmark pairwise similarity
    t_sim_start = time.perf_counter()
    sample_pairs["semantic_similarity"] = compute_chunk_cosine_similarity(sample_pairs, matrix, id_to_idx)
    t_sim = time.perf_counter() - t_sim_start
    sim_throughput = len(sample_pairs) / max(0.001, t_sim)
    
    # 5. Benchmark structural scoring
    t_struct_start = time.perf_counter()
    generic_set = compute_generic_descriptions(df_canonical)
    sample_scored = compute_structural_features(sample_pairs, generic_set)
    sample_scored = compute_duplicate_score(sample_scored)
    t_struct = time.perf_counter() - t_struct_start
    
    total_time = time.perf_counter() - t0
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Full dataset projections
    total_pairs = len(df_pairs)
    total_unique_works = len(set(df_pairs["work_id_1"]).union(set(df_pairs["work_id_2"])))
    all_descriptions = list(set(df_canonical[df_canonical["work_id"].isin(set(df_pairs["work_id_1"]).union(set(df_pairs["work_id_2"])))] ["work_description"].fillna("").astype(str).str.strip()))
    total_unique_descriptions = len(all_descriptions)
    
    projected_embed_time_sec = total_unique_descriptions / max(1.0, embed_throughput)
    projected_sim_time_sec = total_pairs / max(1.0, sim_throughput)
    projected_full_runtime_sec = projected_embed_time_sec + projected_sim_time_sec + 30.0
    
    projected_embed_mem_mb = (total_unique_works * EMBEDDING_DIM * 4) / (1024 * 1024)
    
    results = {
        "subset_size": subset_size,
        "unique_works_in_subset": len(unique_works),
        "unique_descriptions_in_subset": len(unique_descriptions),
        "elapsed_benchmark_seconds": round(total_time, 2),
        "peak_ram_mb": round(peak_mem / (1024 * 1024), 2),
        "embedding_throughput_descs_per_sec": round(embed_throughput, 1),
        "similarity_throughput_pairs_per_sec": round(sim_throughput, 1),
        "total_candidate_pairs": total_pairs,
        "total_unique_works": total_unique_works,
        "total_unique_descriptions": total_unique_descriptions,
        "projected_embedding_time_sec": round(projected_embed_time_sec, 1),
        "projected_similarity_time_sec": round(projected_sim_time_sec, 1),
        "projected_total_runtime_sec": round(projected_full_runtime_sec, 1),
        "projected_embedding_memory_mb": round(projected_embed_mem_mb, 2)
    }
    
    print(f"Benchmark Results: {results}")
    return results
