import numpy as np
import pandas as pd
from typing import Tuple, Dict, Set
from .config import (
    WEIGHT_STRUCT_AMOUNT,
    WEIGHT_STRUCT_DATE,
    WEIGHT_STRUCT_CONST,
    WEIGHT_STRUCT_MP,
    DATE_PROXIMITY_DECAY_DAYS,
    SHORT_DESC_WORD_THRESHOLD,
    GENERIC_DESC_FREQ_THRESHOLD
)

def compute_generic_descriptions(df_works: pd.DataFrame) -> Set[str]:
    """Identifies description strings that appear more than threshold times."""
    desc_series = df_works["work_description"].fillna("").astype(str).str.strip().str.upper()
    counts = desc_series.value_counts()
    generic = set(counts[counts >= GENERIC_DESC_FREQ_THRESHOLD].index)
    generic.discard("")
    return generic

def compute_structural_features(df_pairs: pd.DataFrame, generic_descriptions: Set[str] = None) -> pd.DataFrame:
    """
    Computes additional structural evidence beyond the initial blocking conditions:
      - amount_similarity in [0, 1]
      - date_proximity in [0, 1] (exponential decay)
      - same_constituency (1.0 or 0.0)
      - same_mp (1.0 or 0.0)
      - structural_score in [0, 1]
      - generic_flag and word_count confidence adjustments
    """
    df = df_pairs.copy()
    
    # 1. Amount similarity: 1 - (|amt1 - amt2| / max(amt1, amt2))
    amt1 = df["sanction_amount_1"].values
    amt2 = df["sanction_amount_2"].values
    max_amt = np.maximum(amt1, amt2)
    diff_abs = np.abs(amt1 - amt2)
    amount_sim = np.where(max_amt > 0, 1.0 - (diff_abs / max_amt), 1.0)
    df["amount_similarity"] = np.clip(amount_sim, 0.0, 1.0)
    
    # 2. Date proximity: exp(-days_diff / decay)
    days_diff = df["days_diff"].values
    df["date_proximity"] = np.exp(-days_diff / DATE_PROXIMITY_DECAY_DAYS)
    
    # 3. Same constituency / Same MP
    df["same_const_score"] = df["is_same_constituency"].astype(float)
    df["same_mp_score"] = df["is_same_mp"].astype(float)
    
    # Combined structural component
    df["structural_score"] = (
        WEIGHT_STRUCT_AMOUNT * df["amount_similarity"] +
        WEIGHT_STRUCT_DATE * df["date_proximity"] +
        WEIGHT_STRUCT_CONST * df["same_const_score"] +
        WEIGHT_STRUCT_MP * df["same_mp_score"]
    )
    df["structural_score"] = np.clip(df["structural_score"], 0.0, 1.0)
    
    # 4. Generic and short description flags
    desc1 = df["work_description_1"].fillna("").astype(str).str.strip()
    desc2 = df["work_description_2"].fillna("").astype(str).str.strip()
    
    w1 = desc1.apply(lambda s: len(s.split())).values
    w2 = desc2.apply(lambda s: len(s.split())).values
    
    min_words = np.minimum(w1, w2)
    word_conf = np.clip(min_words / float(SHORT_DESC_WORD_THRESHOLD), 0.2, 1.0)
    df["is_short_description"] = (w1 < SHORT_DESC_WORD_THRESHOLD) | (w2 < SHORT_DESC_WORD_THRESHOLD)
    
    if generic_descriptions is not None:
        is_gen1 = desc1.str.upper().isin(generic_descriptions)
        is_gen2 = desc2.str.upper().isin(generic_descriptions)
        df["is_generic_description"] = is_gen1 | is_gen2
    else:
        df["is_generic_description"] = False
        
    # Dampen confidence if generic
    gen_mult = np.where(df["is_generic_description"], 0.70, 1.0)
    
    # Missing description penalty
    is_missing = (desc1 == "") | (desc2 == "")
    missing_mult = np.where(is_missing, 0.20, 1.0)
    
    df["confidence"] = np.clip(word_conf * gen_mult * missing_mult, 0.1, 1.0)
    
    return df
