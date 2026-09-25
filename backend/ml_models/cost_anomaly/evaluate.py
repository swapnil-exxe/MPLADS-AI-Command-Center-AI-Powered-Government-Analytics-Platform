import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def evaluate_model1_results(df_scored: pd.DataFrame, top_k: int = 50) -> Dict[str, Any]:
    """
    Performs empirical evaluation of Model 1 results:
      1. Top-K review sample extraction
      2. Severity distribution check
      3. Data quality exception routing verification
      4. Stability check across peer levels
    """
    logging.info("Evaluating Model 1 cost anomaly detection performance & distributions...")
    
    total_works = len(df_scored)
    
    # 1. Top-K Anomaly Review Sample
    df_valid = df_scored[df_scored["severity"] != "DATA_QUALITY_EXCEPTION"].copy()
    top_k_anomalies = df_valid.sort_values("cost_anomaly_score", ascending=False).head(top_k)
    
    top_k_summary = []
    for _, r in top_k_anomalies.iterrows():
        top_k_summary.append({
            "work_id": r["work_id"],
            "state": r["state"],
            "district": r["district"],
            "work_type_template": r["work_type_template"],
            "sanction_amount": float(r["sanction_amount"]),
            "peer_median_amount": float(r.get("model_peer_median_amount", 0.0)),
            "cost_ratio_vs_peer_median": float(r.get("cost_ratio_vs_peer_median", 1.0)),
            "cost_anomaly_score": float(r["cost_anomaly_score"]),
            "severity": r["severity"],
            "peer_group_used": r["peer_group_used"],
            "explanation": r.get("explanation", "")
        })
        
    # 2. Severity Distribution Summary
    sev_counts = df_scored["severity"].value_counts().to_dict()
    sev_pcts = {k: float((v / total_works) * 100.0) for k, v in sev_counts.items()}
    
    # 3. Data Quality Exception Routing Check
    dq_count = int(df_scored["is_data_quality_exception"].sum())
    dq_routed_count = int((df_scored["severity"] == "DATA_QUALITY_EXCEPTION").sum())
    dq_routing_passed = (dq_count == dq_routed_count)
    
    # 4. Peer Level Distribution
    level_counts = df_scored["peer_group_level"].value_counts().to_dict()
    
    results = {
        "total_works": total_works,
        "severity_counts": sev_counts,
        "severity_percentages": sev_pcts,
        "data_quality_exceptions_total": dq_count,
        "data_quality_exceptions_routed": dq_routed_count,
        "data_quality_routing_passed": dq_routing_passed,
        "peer_group_level_counts": level_counts,
        "top_k_anomalies": top_k_summary
    }
    
    logging.info(f"Evaluation Complete: HIGH Severity = {sev_counts.get('HIGH', 0):,} ({sev_pcts.get('HIGH', 0.0):.2f}%), MEDIUM = {sev_counts.get('MEDIUM', 0):,}, LOW = {sev_counts.get('LOW', 0):,}")
    return results
