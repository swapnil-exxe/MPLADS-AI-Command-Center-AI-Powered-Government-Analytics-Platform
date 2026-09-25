import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from sentence_transformers import SentenceTransformer
from .config import MODEL_NAME, EMBEDDING_DIM, EMBEDDING_BATCH_SIZE, EMBEDDINGS_CACHE_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

import os
import torch

def get_sentence_transformer(model_name: str = MODEL_NAME) -> SentenceTransformer:
    """Loads lightweight SentenceTransformer model."""
    threads = min(8, os.cpu_count() or 4)
    torch.set_num_threads(threads)
    logging.info(f"Loading SentenceTransformer: {model_name} (torch threads={threads})")
    return SentenceTransformer(model_name)

def generate_unique_work_embeddings(
    work_ids: List[str],
    df_canonical: pd.DataFrame,
    model: SentenceTransformer,
    cache_path: Optional[Path] = EMBEDDINGS_CACHE_PATH,
    batch_size: int = EMBEDDING_BATCH_SIZE
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    CRITICAL ARCHITECTURE: Generates ONE embedding per unique work description.
    Never encodes descriptions redundantly for every candidate pair.
    
    Returns:
      embeddings_matrix: np.ndarray (N_works, 384), float32, L2-normalized
      work_id_to_idx: Dict mapping work_id -> row index in matrix
    """
    # Check if cache exists
    if cache_path and cache_path.exists():
        logging.info(f"Loading cached embeddings from {cache_path}...")
        data = np.load(cache_path, allow_pickle=True)
        cached_ids = list(data["work_ids"])
        cached_set = set(cached_ids)
        # Verify all required work_ids are present in cache
        if set(work_ids).issubset(cached_set):
            logging.info(f"Cache hit! Loaded {len(cached_ids):,} embeddings from cache.")
            id_to_idx = {wid: i for i, wid in enumerate(cached_ids)}
            return data["embeddings"], id_to_idx

    # Match work_ids with descriptions from canonical layer
    canonical_map = df_canonical.set_index("work_id")["work_description"].to_dict()
    
    unique_ids = sorted(list(set(work_ids)))
    descriptions = [canonical_map.get(wid, "") for wid in unique_ids]
    clean_descs = [str(d).strip() if pd.notna(d) else "" for d in descriptions]
    
    # Deduplicate descriptions across works to minimize transformer forward passes
    unique_descs = list(set(clean_descs))
    logging.info(f"Encoding {len(unique_descs):,} unique descriptions for {len(unique_ids):,} unique works...")
    
    desc_embeddings = model.encode(
        unique_descs,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    ).astype(np.float32)
    
    desc_to_emb = {desc: desc_embeddings[i] for i, desc in enumerate(unique_descs)}
    
    # Build matrix for all unique work IDs
    n_works = len(unique_ids)
    embeddings_matrix = np.zeros((n_works, EMBEDDING_DIM), dtype=np.float32)
    id_to_idx = {}
    
    for i, wid in enumerate(unique_ids):
        desc = clean_descs[i]
        emb = desc_to_emb.get(desc, np.zeros(EMBEDDING_DIM, dtype=np.float32))
        embeddings_matrix[i] = emb
        id_to_idx[wid] = i
        
    # Save cache if path provided
    if cache_path:
        logging.info(f"Saving embeddings cache ({n_works:,} works) to {cache_path}...")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cache_path,
            work_ids=np.array(unique_ids),
            embeddings=embeddings_matrix
        )
        
    return embeddings_matrix, id_to_idx
