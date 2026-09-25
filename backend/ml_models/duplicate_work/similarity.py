import numpy as np
import pandas as pd
from typing import Dict

def compute_chunk_cosine_similarity(
    df_chunk: pd.DataFrame,
    embeddings_matrix: np.ndarray,
    work_id_to_idx: Dict[str, int]
) -> np.ndarray:
    """
    Computes vectorized cosine similarity for a chunk of candidate pairs.
    Because embeddings are L2-normalized, cosine similarity is the dot product.
    """
    w1_ids = df_chunk["work_id_1"].values
    w2_ids = df_chunk["work_id_2"].values
    
    n = len(df_chunk)
    idx1 = np.array([work_id_to_idx.get(wid, -1) for wid in w1_ids], dtype=np.int32)
    idx2 = np.array([work_id_to_idx.get(wid, -1) for wid in w2_ids], dtype=np.int32)
    
    valid_mask = (idx1 >= 0) & (idx2 >= 0)
    
    # Extract vectors
    emb1 = np.zeros((n, embeddings_matrix.shape[1]), dtype=np.float32)
    emb2 = np.zeros((n, embeddings_matrix.shape[1]), dtype=np.float32)
    
    emb1[valid_mask] = embeddings_matrix[idx1[valid_mask]]
    emb2[valid_mask] = embeddings_matrix[idx2[valid_mask]]
    
    # Vectorized dot product (cosine similarity)
    similarities = np.sum(emb1 * emb2, axis=1)
    
    # Clamp to [0.0, 1.0]
    return np.clip(similarities, 0.0, 1.0)
