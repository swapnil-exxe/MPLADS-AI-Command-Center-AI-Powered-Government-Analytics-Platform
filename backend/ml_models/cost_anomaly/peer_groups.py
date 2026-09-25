import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any

from .config import PEER_MIN_GROUP_SIZE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def assign_hierarchical_peer_groups(
    df: pd.DataFrame,
    min_group_size: int = PEER_MIN_GROUP_SIZE
) -> pd.DataFrame:
    """
    Implements deterministic hierarchical peer-group assignment:
      1. State x Work Type (Level 1 - Fine)
      2. National Work Type (Level 2 - Coarse)
      3. National Overall (Level 3 - National)
      
    Annotates DataFrame with:
      - peer_group_used
      - peer_group_level
      - peer_group_size
      - is_sufficient_data_flag
    """
    logging.info(f"Assigning hierarchical peer groups with minimum group size threshold N = {min_group_size}...")
    
    out = df.copy()
    
    out["state_clean"] = out["state"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    out["template_clean"] = out["work_type_template"].fillna("UNCLASSIFIED").astype(str).str.strip()
    
    # Define keys
    out["group_key_fine"] = out["state_clean"] + " || " + out["template_clean"]
    out["group_key_coarse"] = out["template_clean"]
    
    # Calculate group sizes at each level
    fine_counts = out["group_key_fine"].value_counts().to_dict()
    coarse_counts = out["group_key_coarse"].value_counts().to_dict()
    national_count = len(out)
    
    group_used = []
    group_level = []
    group_size = []
    sufficient_flag = []
    
    for idx, row in out.iterrows():
        k_fine = row["group_key_fine"]
        k_coarse = row["group_key_coarse"]
        
        sz_fine = fine_counts.get(k_fine, 0)
        sz_coarse = coarse_counts.get(k_coarse, 0)
        
        if sz_fine >= min_group_size:
            group_used.append(k_fine)
            group_level.append("STATE_WORK_TYPE")
            group_size.append(sz_fine)
            sufficient_flag.append(True)
        elif sz_coarse >= min_group_size:
            group_used.append(k_coarse)
            group_level.append("NATIONAL_WORK_TYPE")
            group_size.append(sz_coarse)
            sufficient_flag.append(True)
        elif national_count >= min_group_size:
            group_used.append("NATIONAL_OVERALL")
            group_level.append("NATIONAL_OVERALL")
            group_size.append(national_count)
            sufficient_flag.append(True)
        else:
            group_used.append("INSUFFICIENT_DATA")
            group_level.append("INSUFFICIENT_PEER_DATA")
            group_size.append(national_count)
            sufficient_flag.append(False)
            
    out["peer_group_used"] = group_used
    out["peer_group_level"] = group_level
    out["peer_group_size"] = group_size
    out["is_sufficient_peer_data"] = sufficient_flag
    
    level_counts = out["peer_group_level"].value_counts().to_dict()
    logging.info(f"Peer Group Assignment complete: {level_counts}")
    return out
