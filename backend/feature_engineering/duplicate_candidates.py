import logging
import pandas as pd
import numpy as np
from typing import Tuple

from .config import DUPLICATE_BLOCKING_WINDOW_DAYS, DUPLICATE_AMOUNT_RATIO_THRESHOLD

def generate_duplicate_candidate_pairs(df_works: pd.DataFrame) -> pd.DataFrame:
    """
    Generates candidate work pairs for Model 2 (Duplicate Work Detection).
    Applies strict blocking conditions to make pairwise comparison computationally tractable:
      1. Same district
      2. Same work_type_template
      3. Sanction date within 90 days (abs(date1 - date2) <= 90)
      4. Sanction amount ratio >= 0.70 (amount similarity floor)
      5. work_id_1 < work_id_2 (unordered unique pairs)
      
    Uses vectorized NumPy searchsorted and array indexing for sub-second performance.
    """
    logging.info("Generating candidate work pairs for Model 2 Duplicate Work Detection...")
    
    df = df_works.copy()
    
    # Filter works with valid sanction date, district, and work_type_template
    valid_mask = (
        df["work_id"].notna() &
        df["district"].notna() &
        df["work_type_template"].notna() &
        df["sanction_date"].notna()
    )
    df_valid = df[valid_mask].copy()
    
    df_valid["sanction_dt"] = pd.to_datetime(df_valid["sanction_date"], errors="coerce")
    df_valid = df_valid[df_valid["sanction_dt"].notna()]
    
    df_valid["block_key"] = df_valid["district"].astype(str).str.strip().str.upper() + " || " + df_valid["work_type_template"].astype(str).str.strip()
    
    pairs = []
    
    # Group by block_key and find candidate pairs within 90-day window using NumPy vectorization
    for block_key, group in df_valid.groupby("block_key"):
        if len(group) < 2:
            continue
            
        group_sorted = group.sort_values("sanction_dt")
        work_ids = group_sorted["work_id"].values
        sanction_dts = group_sorted["sanction_dt"].values
        amounts = group_sorted["sanction_amount"].fillna(0.0).values
        mps = group_sorted["mp_name"].values if "mp_name" in group_sorted.columns else np.array([None] * len(group_sorted))
        consts = group_sorted["constituency_or_term"].values if "constituency_or_term" in group_sorted.columns else np.array([None] * len(group_sorted))
        houses = group_sorted["house"].values if "house" in group_sorted.columns else np.array([None] * len(group_sorted))
        districts = group_sorted["district"].values
        templates = group_sorted["work_type_template"].values
        sanc_str_dates = group_sorted["sanction_date"].values
        descriptions = group_sorted["work_description"].values if "work_description" in group_sorted.columns else np.array([""] * len(group_sorted))
        
        # Calculate search boundaries for 90 days window
        window_ns = np.timedelta64(DUPLICATE_BLOCKING_WINDOW_DAYS, "D")
        max_dts = sanction_dts + window_ns
        end_indices = np.searchsorted(sanction_dts, max_dts, side="right")
        
        n = len(group_sorted)
        for i in range(n):
            j_end = end_indices[i]
            if j_end <= i + 1:
                continue
                
            j_indices = np.arange(i + 1, j_end)
            amt1 = amounts[i]
            amt2_vec = amounts[j_indices]
            
            max_amt = np.maximum(amt1, amt2_vec)
            min_amt = np.minimum(amt1, amt2_vec)
            amt_ratio_vec = np.where(max_amt > 0, min_amt / max_amt, 0.0)
            
            # Vectorized filter for ratio >= DUPLICATE_AMOUNT_RATIO_THRESHOLD (0.90)
            match_mask = amt_ratio_vec >= DUPLICATE_AMOUNT_RATIO_THRESHOLD
            if not np.any(match_mask):
                continue
                
            valid_j = j_indices[match_mask]
            id1 = work_ids[i]
            dt1 = sanction_dts[i]
            mp1 = mps[i]
            const1 = consts[i]
            house1 = houses[i]
            dist1 = districts[i]
            tmpl1 = templates[i]
            sanc_str1 = sanc_str_dates[i]
            desc1 = descriptions[i]
            
            for idx_in_vj, j in enumerate(valid_j):
                id2 = work_ids[j]
                dt2 = sanction_dts[j]
                amt2 = amounts[j]
                amt_ratio = float(amt_ratio_vec[match_mask][idx_in_vj])
                
                mp2 = mps[j]
                const2 = consts[j]
                house2 = houses[j]
                sanc_str2 = sanc_str_dates[j]
                desc2 = descriptions[j]
                
                days_diff = int((dt2 - dt1) / np.timedelta64(1, "D"))
                
                if id1 > id2:
                    id_a, id_b = id2, id1
                    house_a, house_b = house2, house1
                    sanc_str_a, sanc_str_b = sanc_str2, sanc_str1
                    amt_a, amt_b = amt2, amt1
                    mp_a, mp_b = mp2, mp1
                    const_a, const_b = const2, const1
                    desc_a, desc_b = desc2, desc1
                else:
                    id_a, id_b = id1, id2
                    house_a, house_b = house1, house2
                    sanc_str_a, sanc_str_b = sanc_str1, sanc_str2
                    amt_a, amt_b = amt1, amt2
                    mp_a, mp_b = mp1, mp2
                    const_a, const_b = const1, const2
                    desc_a, desc_b = desc1, desc2
                    
                is_same_mp = (mp_a == mp_b) if (pd.notna(mp_a) and pd.notna(mp_b)) else False
                is_same_const = (const_a == const_b) if (pd.notna(const_a) and pd.notna(const_b)) else False
                
                pairs.append({
                    "work_id_1": id_a,
                    "work_id_2": id_b,
                    "house_1": house_a,
                    "house_2": house_b,
                    "district": dist1,
                    "work_type_template": tmpl1,
                    "sanction_date_1": sanc_str_a,
                    "sanction_date_2": sanc_str_b,
                    "days_diff": days_diff,
                    "sanction_amount_1": float(amt_a),
                    "sanction_amount_2": float(amt_b),
                    "amount_diff_abs": float(abs(amt_a - amt_b)),
                    "amount_ratio": amt_ratio,
                    "is_amount_within_10pct": amt_ratio >= DUPLICATE_AMOUNT_RATIO_THRESHOLD,
                    "mp_name_1": mp_a,
                    "mp_name_2": mp_b,
                    "is_same_mp": is_same_mp,
                    "constituency_1": const_a,
                    "constituency_2": const_b,
                    "is_same_constituency": is_same_const,
                    "work_description_1": desc_a,
                    "work_description_2": desc_b,
                })
                
    df_pairs = pd.DataFrame(pairs)
    logging.info(f"Generated {len(df_pairs):,} duplicate candidate pairs after blocking.")
    return df_pairs
