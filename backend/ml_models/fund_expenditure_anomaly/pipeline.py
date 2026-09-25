import time
import pandas as pd
from datetime import datetime
from .config import Model3Config
from .features import FeatureEngineer
from .model import FundIsolationForest
from .score import CalibratedScorer
from .explain import ExplanationGenerator
from .evaluate import Model3Evaluator
from .artifacts import ArtifactManager

def run_fund_expenditure_pipeline(config: Model3Config = None) -> pd.DataFrame:
    """Executes end-to-end Model 3 Fund & Expenditure Anomaly Detection pipeline."""
    t0 = time.time()
    if config is None:
        config = Model3Config()

    print(f"=== Running Phase 4.3 — Model 3 Pipeline ===")
    print(f"Loading features from: {config.features_path}")
    raw_df = pd.read_parquet(config.features_path)
    print(f"Loaded {len(raw_df)} works.")

    # 1. Feature Engineering
    fe = FeatureEngineer(config)
    df_all, df_active, df_zero, X_scaled = fe.prepare_data(raw_df)
    print(f"Active financial works: {len(df_active)}, Zero-disbursement works: {len(df_zero)}")

    # 2. Model Training & Raw Scoring
    model = FundIsolationForest(config)
    print("Training Isolation Forest on active cohort...")
    model.fit(X_scaled)
    s_raw_active = model.raw_anomaly_scores(X_scaled)
    print(f"Active scoring complete. Raw scores: min={s_raw_active.min():.4f}, median={pd.Series(s_raw_active).median():.4f}, max={s_raw_active.max():.4f}")

    # 3. Score Calibration & Integration
    scorer = CalibratedScorer(config)
    scored_df = scorer.score_all(df_active, s_raw_active, df_zero)

    # 4. Explanation Generation
    print("Generating transparent, auditable explanations...")
    explainer = ExplanationGenerator(config)
    reasons_list = []
    explanations_list = []
    for idx, row in scored_df.iterrows():
        reasons, expl = explainer.generate_reasons_and_explanation(row)
        reasons_list.append(reasons)
        explanations_list.append(expl)

    scored_df["anomaly_reasons"] = reasons_list
    scored_df["explanation"] = explanations_list

    # Ensure canonical work order
    scored_df = scored_df.sort_values("work_id").reset_index(drop=True)

    # 5. Evaluation
    evaluator = Model3Evaluator()
    metrics = evaluator.evaluate(scored_df)
    runtime = time.time() - t0
    metrics["runtime_seconds"] = round(runtime, 2)
    metrics["timestamp"] = datetime.now().isoformat()

    print(f"\nPipeline execution finished in {runtime:.2f}s")
    print(f"Severity Breakdown: {metrics['severity_counts']} ({metrics['severity_pct']})")

    # 6. Artifact Serialization
    am = ArtifactManager(config)
    am.save_scores(scored_df)
    am.save_model(model.model, fe.scaler)
    am.save_metadata(metrics)
    print(f"Saved scores to: {config.scores_output_path}")
    print(f"Saved model & scaler to: {config.model_save_dir}")

    # 7. Write Markdown Report
    _write_report(config.report_output_path, metrics)
    print(f"Report written to: {config.report_output_path}")

    return scored_df

def _write_report(report_path, metrics):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    md = f"""# Model 3: Fund & Expenditure Anomaly Detector Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Phase**: Phase 4.3 — Model 3 (Fund & Expenditure Anomaly)  
**Date**: {metrics['timestamp'][:10]}  
**Status**: `MODEL 3 COMPLETE`  

---

## 1. Executive Summary
Model 3 evaluates the financial flow and expenditure patterns of MPLADS works to detect anomalous fund utilization, unusual tranche fragmentation, disbursement timing latencies, and administrative status-expenditure mismatches.

## 2. Dataset & Cohort Segmentation
* **Total Works Analyzed**: {metrics['total_works']:,}
* **Active Financial Cohort (Disbursed > 0)**: {metrics['active_works_count']:,} (72.8%)
* **Zero-Disbursement Cohort**: {metrics['zero_spend_works_count']:,} (27.2%)
* **Execution Runtime**: {metrics['runtime_seconds']} seconds

## 3. Severity Distribution
| Severity Tier | Work Count | Share % | Definition / Administrative Action |
|---|---|---|---|
| `LOW` | {metrics['severity_counts'].get('LOW', 0):,} | {metrics['severity_pct'].get('LOW', 0.0)}% | Normal expenditure flow / newly sanctioned awaiting release |
| `MEDIUM` | {metrics['severity_counts'].get('MEDIUM', 0):,} | {metrics['severity_pct'].get('MEDIUM', 0.0)}% | Watchlist: Elevated anomaly score or dormant sanction (>365 days) |
| `HIGH` | {metrics['severity_counts'].get('HIGH', 0):,} | {metrics['severity_pct'].get('HIGH', 0.0)}% | High Priority: Top multi-variate outlier or status-expenditure mismatch |

## 4. Audit Category Breakdown
| Audit Category | Count | Description |
|---|---|---|
| `ACTIVE_EXPENDITURE` | {metrics['audit_category_counts'].get('ACTIVE_EXPENDITURE', 0):,} | Evaluated via Isolation Forest on continuous financial features |
| `NORMAL_AWAITING_DISBURSEMENT` | {metrics['audit_category_counts'].get('NORMAL_AWAITING_DISBURSEMENT', 0):,} | Early stage (Sanction/Vendor ID) <= 365 days old |
| `DORMANT_SANCTION` | {metrics['audit_category_counts'].get('DORMANT_SANCTION', 0):,} | Sanctioned > 365 days ago with zero fund disbursement |
| `STATUS_EXPENDITURE_MISMATCH` | {metrics['audit_category_counts'].get('STATUS_EXPENDITURE_MISMATCH', 0):,} | Completed / Physical Inspection with zero expenditure vouchers |

## 5. Active Cohort Calibrated Score Percentiles
* **p0 (Min)**: {metrics['active_score_percentiles']['p0']}
* **p50 (Median)**: {metrics['active_score_percentiles']['p50']}
* **p75**: {metrics['active_score_percentiles']['p75']}
* **p90**: {metrics['active_score_percentiles']['p90']}
* **p95**: {metrics['active_score_percentiles']['p95']}
* **p97 (Decision Cutoff)**: {metrics['active_score_percentiles']['p97']}
* **p99**: {metrics['active_score_percentiles']['p99']}
* **p100 (Max)**: {metrics['active_score_percentiles']['p100']}

## 6. Sample Top Anomalies
| Work ID | State | Status | Sanction Amount | Disbursed Amount | Utilization | Tranches | Score | Severity |
|---|---|---|---|---|---|---|---|---|
"""
    for item in metrics["top_anomalies_sample"]:
        md += f"| `{item['work_id']}` | {item['state']} | {item['work_status']} | ₹{item['sanction_amount']:,.2f} | ₹{item['total_disbursed_amount']:,.2f} | {item['utilization_ratio']*100:.1f}% | {item['transaction_count']} | `{item['fund_anomaly_score']:.2f}` | `{item['severity']}` |\n"

    md += """
## 7. Model Artifacts
* **Scored Output Dataset**: `data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet`
* **Trained Model**: `models/fund_expenditure_anomaly/isolation_forest.joblib`
* **Robust Scaler**: `models/fund_expenditure_anomaly/robust_scaler.joblib`
* **Metadata JSON**: `models/fund_expenditure_anomaly/model_metadata.json`
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    run_fund_expenditure_pipeline()
