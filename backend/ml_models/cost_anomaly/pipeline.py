import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

from .config import (
    COST_FEATURES_PATH,
    MODEL_OUTPUTS_DIR,
    OUTPUT_PARQUET_PATH,
    MODELS_DIR,
    REPORT_PATH,
)
from .preprocessing import validate_input_schema, assert_zero_leakage
from .peer_groups import assign_hierarchical_peer_groups
from .train import train_peer_isolation_forests
from .score import score_works_dataset
from .explain import attach_explanations
from .evaluate import evaluate_model1_results
from .artifacts import save_model_artifacts, save_scored_output_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def generate_markdown_report(eval_results: Dict[str, Any], report_path: Path = REPORT_PATH) -> Path:
    """
    Generates the final Model 1 Cost Anomaly Detection Report.
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_works = eval_results["total_works"]
    sev_counts = eval_results["severity_counts"]
    sev_pcts = eval_results["severity_percentages"]
    level_counts = eval_results["peer_group_level_counts"]
    top_k = eval_results["top_k_anomalies"]
    
    md = []
    md.append("# Phase 4.1 — Model 1: Anomalous Cost Estimate Detector Report")
    md.append("**Model Name**: Model 1 (Anomalous Cost Estimate Detector)  ")
    md.append("**Model Version**: `cost_anomaly_v1`  ")
    md.append("**Status**: `MODEL 1 COMPLETE`  \n")
    md.append("---\n")
    
    md.append("## 1. Executive Summary")
    md.append("Model 1 evaluates the reasonableness of sanctioned/estimated costs for MPLADS works using an unsupervised, hierarchical peer-grouped **Isolation Forest** model. It operates strictly at sanction time with **zero post-sanction leakage**.\n")
    
    md.append("## 2. Dataset & Zero-Leakage Verification")
    md.append(f"- **Input File**: `data/features/cost/cost_anomaly_features.parquet`")
    md.append(f"- **Total Sanctioned Works Analyzed**: {total_works:,} rows")
    md.append(f"- **Zero-Leakage Assertion**: `PASSED` (0 post-sanction columns used)\n")
    
    md.append("## 3. Hierarchical Peer Grouping & Fallback Breakdown")
    md.append("Works are grouped hierarchically to compare costs against natural peer groups (e.g. Street Lights vs Roads):")
    md.append("| Peer Group Level | Description | Work Count | Share % |")
    md.append("|---|---|---|---|")
    for lvl, cnt in level_counts.items():
        pct = (cnt / total_works) * 100.0
        md.append(f"| `{lvl}` | {lvl.replace('_', ' ').title()} | {cnt:,} | {pct:.2f}% |")
    md.append("\n")
    
    md.append("## 4. Anomaly Severity Distribution")
    md.append("Scores are normalized into a calibrated `[0.0, 1.0]` interval using sigmoid mapping centered at decision boundary 0.0:")
    md.append("| Severity | Score Range / Rule | Count | Share % | Action / Framing |")
    md.append("|---|---|---|---|---|")
    md.append(f"| `HIGH` | $\\ge 0.75$ | {sev_counts.get('HIGH', 0):,} | {sev_pcts.get('HIGH', 0.0):.2f}% | High priority review |")
    md.append(f"| `MEDIUM` | $0.50 \\le \\text{{score}} < 0.75$ | {sev_counts.get('MEDIUM', 0):,} | {sev_pcts.get('MEDIUM', 0.0):.2f}% | Standard audit |")
    md.append(f"| `LOW` | $< 0.50$ | {sev_counts.get('LOW', 0):,} | {sev_pcts.get('LOW', 0.0):.2f}% | Normal cost estimate |")
    md.append(f"| `DATA_QUALITY_EXCEPTION` | $< ₹1,000$ sanction amount | {sev_counts.get('DATA_QUALITY_EXCEPTION', 0):,} | {sev_pcts.get('DATA_QUALITY_EXCEPTION', 0.0):.2f}% | Data entry correction flag |")
    md.append("\n")
    
    md.append("## 5. Top 10 High Cost-Anomaly Sample Review")
    md.append("| Work ID | State | Work Type | Sanction Amount | Peer Median | Relative Deviation | Score | Severity |")
    md.append("|---|---|---|---|---|---|---|---|")
    for r in top_k[:10]:
        sanc_str = f"₹{r['sanction_amount']:,.2f}"
        med_str = f"₹{r['peer_median_amount']:,.2f}"
        ratio = r['cost_ratio_vs_peer_median']
        dev_pct = (ratio - 1.0) * 100.0
        dev_str = f"+{dev_pct:.1f}%" if dev_pct >= 0 else f"{dev_pct:.1f}%"
        md.append(f"| `{r['work_id']}` | {r['state']} | `{r['work_type_template'][:30]}` | {sanc_str} | {med_str} | **{dev_str}** | `{r['cost_anomaly_score']:.2f}` | `{r['severity']}` |")
    md.append("\n")
    
    md.append("## 6. Sample Auditable Explanation")
    if top_k:
        md.append(f"> {top_k[0]['explanation']}\n")
        
    md.append("## 7. Model Artifacts & Outputs")
    md.append("- **Scored Output Parquet**: `data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet`")
    md.append("- **Global Model Metadata**: `models/cost_anomaly/global_model_metadata.json`")
    md.append("- **Trained Peer Models**: `models/cost_anomaly/peer_models/*.joblib`\n")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
        
    logging.info(f"Exported Model 1 Markdown Report to {report_path}")
    return report_path

def run_model1_pipeline(input_parquet: Path = COST_FEATURES_PATH) -> Dict[str, Any]:
    """
    Executes the full Phase 4.1 Model 1 Pipeline:
      Phase 3 Features -> Validation -> Zero Leakage -> Peer Grouping -> Training -> Scoring -> Explanation -> Evaluation -> Artifacts.
    """
    logging.info("Starting Phase 4.1 Model 1 Pipeline (Anomalous Cost Estimate Detector)...")
    
    # 1. Load Data
    df_raw = pd.read_parquet(input_parquet)
    logging.info(f"Loaded {len(df_raw):,} rows from {input_parquet}")
    
    # 2. Input Validation
    validate_input_schema(df_raw)
    
    # 3. Zero Leakage Assertion
    assert_zero_leakage(df_raw)
    
    # 4. Peer Group Assignment
    df_annotated = assign_hierarchical_peer_groups(df_raw)
    
    # 5. Train Isolation Forests per Peer Group
    peer_models = train_peer_isolation_forests(df_annotated)
    
    # 6. Score Dataset & Normalize
    df_scored = score_works_dataset(df_annotated, peer_models)
    
    # 7. Attach Explanations
    df_final = attach_explanations(df_scored)
    
    # 8. Evaluate
    eval_results = evaluate_model1_results(df_final, top_k=50)
    
    # 9. Save Artifacts
    meta_path = save_model_artifacts(peer_models, total_training_works=len(df_final))
    
    # 10. Save Output Parquet
    parquet_path = save_scored_output_parquet(df_final)
    
    # 11. Generate Markdown Report
    report_path = generate_markdown_report(eval_results)
    
    logging.info("Phase 4.1 Model 1 Pipeline completed successfully!")
    return {
        "df_scored": df_final,
        "peer_models": peer_models,
        "eval_results": eval_results,
        "meta_path": meta_path,
        "parquet_path": parquet_path,
        "report_path": report_path
    }

if __name__ == "__main__":
    run_model1_pipeline()
