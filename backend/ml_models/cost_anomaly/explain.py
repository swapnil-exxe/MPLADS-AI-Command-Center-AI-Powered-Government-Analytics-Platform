import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def generate_work_explanation(row: pd.Series) -> str:
    """
    Generates a structured, human-readable, auditable explanation for a scored work.
    Frame: REQUIRES REVIEW / ANOMALOUS ESTIMATE (Never 'FRAUD CONFIRMED').
    """
    wid = row.get("work_id", "UNKNOWN")
    sanc_amt = float(row.get("sanction_amount", 0.0) or 0.0)
    peer_med = float(row.get("model_peer_median_amount", row.get("peer_median_amount", 0.0)) or 0.0)
    peer_grp = str(row.get("peer_group_used", "UNKNOWN"))
    peer_sz = int(row.get("peer_group_size", 0) or 0)
    score = float(row.get("cost_anomaly_score", 0.0) or 0.0)
    sev = str(row.get("severity", "LOW"))
    is_dq = bool(row.get("is_data_quality_exception", False))
    
    if is_dq:
        return (
            f"Work ID {wid} has a sanction amount of ₹{sanc_amt:,.2f}, which is below the ₹1,000.00 floor exception threshold. "
            f"Routed to Data Quality Exception review."
        )
        
    if peer_med > 0:
        rel_dev_pct = ((sanc_amt - peer_med) / peer_med) * 100.0
        sign_str = f"+{rel_dev_pct:.1f}%" if rel_dev_pct >= 0 else f"{rel_dev_pct:.1f}%"
    else:
        sign_str = "N/A"
        
    explanation = (
        f"Work ID: {wid} | Sanction Amount: ₹{sanc_amt:,.2f} ({sign_str} vs peer median ₹{peer_med:,.2f}) | "
        f"Peer Group: '{peer_grp}' (N={peer_sz:,}) | Cost Anomaly Score: {score:.2f} | Severity: {sev} — REQUIRES REVIEW."
    )
    return explanation

def attach_explanations(df_scored: pd.DataFrame) -> pd.DataFrame:
    """
    Attaches structured explanations to all scored works in the DataFrame.
    """
    logging.info("Generating auditable explanations for scored works...")
    out = df_scored.copy()
    explanations = [generate_work_explanation(row) for _, row in out.iterrows()]
    out["explanation"] = explanations
    return out
