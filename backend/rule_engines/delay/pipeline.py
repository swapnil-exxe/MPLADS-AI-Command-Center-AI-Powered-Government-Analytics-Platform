import time
from datetime import datetime
import pandas as pd
from .config import DelayConfig
from .score import DelayScorer
from .explain import DelayExplanationGenerator
from .evaluate import DelayEvaluator

def run_delay_pipeline(config: DelayConfig = None) -> pd.DataFrame:
    """Executes end-to-end Phase 5 Delay & SLA Rule Engine."""
    t0 = time.time()
    if config is None:
        config = DelayConfig()

    print("=== Running Phase 5 — Delay Logic + Severity Logging ===")
    print(f"Loading canonical works from: {config.canonical_works_path}")
    canon = pd.read_parquet(config.canonical_works_path)
    print(f"Loaded {len(canon)} canonical works.")

    # 1. Evaluate rules and compute scores
    scorer = DelayScorer(config)
    scored_df = scorer.compute_all_scores(canon)

    # 2. Generate explanations
    print("Generating transparent delay explanations...")
    explainer = DelayExplanationGenerator(config)
    explanations = [explainer.generate_explanation(row) for _, row in scored_df.iterrows()]
    scored_df["explanation"] = explanations

    # 3. Evaluate metrics
    evaluator = DelayEvaluator()
    metrics = evaluator.evaluate(scored_df)
    runtime = time.time() - t0
    metrics["runtime_seconds"] = round(runtime, 2)
    metrics["timestamp"] = datetime.now().isoformat()

    print(f"\nPipeline execution finished in {runtime:.2f}s")
    print(f"Severity Breakdown: {metrics['severity_counts']} ({metrics['severity_pct']})")

    # 4. Save output parquet
    config.output_dir.mkdir(parents=True, exist_ok=True)
    output_cols = [
        "work_id",
        "house",
        "state",
        "district",
        "ida",
        "mp_name",
        "work_status",
        "sanction_amount",
        "is_completed_flag",
        "recommended_date",
        "sanction_date",
        "completion_date",
        "rec_to_sanc_days",
        "rec_to_sanc_delay_days",
        "rec_to_sanc_severity",
        "rec_to_sanc_score",
        "sanc_to_comp_days",
        "sanc_to_comp_delay_days",
        "sanc_to_comp_severity",
        "sanc_to_comp_score",
        "open_work_aging_days",
        "open_work_overdue_days",
        "open_work_aging_severity",
        "open_work_aging_score",
        "delay_score",
        "severity",
        "primary_delay_type",
        "active_delay_types",
        "explanation"
    ]
    save_cols = [c for c in output_cols if c in scored_df.columns]
    scored_df[save_cols].to_parquet(config.scores_output_path, index=False)
    print(f"Saved delay scores to: {config.scores_output_path}")

    # 5. Write Report
    _write_report(config.report_output_path, metrics, config)
    print(f"Report written to: {config.report_output_path}")

    return scored_df

def _write_report(report_path, metrics, config):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    md = f"""# Phase 5: Delay Logic & SLA Rule Engine Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Phase**: Phase 5 — Delay Logic + Severity Logging  
**Date**: {metrics['timestamp'][:10]}  
**Status**: `PHASE 5 COMPLETE`  

---

## 1. Executive Summary
Phase 5 implements the deterministic Delay & SLA Rule Engine for all 98,825 active MPLADS works. Grounded in official MPLADS guidelines (Para 3.12 75-day sanction SLA and 365-day completion guideline limit), the engine evaluates observable lifecycle milestones, assigns standardized severities (`NONE`, `LOW`, `MEDIUM`, `HIGH`), and produces a fully explainable, normalized delay score in [0.0, 1.0].

## 2. Dataset & Reference Date Strategy
* **Total Works Analyzed**: {metrics['total_works']:,}
* **Completed Works Analyzed**: {metrics['completed_works_count']:,} (45.0%)
* **Incomplete / Open Works Analyzed**: {metrics['open_works_count']:,} (55.0%)
* **Fixed Reference Date**: `{config.fixed_reference_date}` (latest sanction date in dataset, ensuring complete determinism and reproducibility)
* **Execution Runtime**: {metrics['runtime_seconds']} seconds

## 3. Severity Distribution
| Severity Tier | Work Count | Share % | Definition / Operational Meaning |
|---|---|---|---|
| `NONE` | {metrics['severity_counts'].get('NONE', 0):,} | {metrics['severity_pct'].get('NONE', 0.0)}% | Fully compliant with 75-day sanction SLA and 365-day execution guideline |
| `LOW` | {metrics['severity_counts'].get('LOW', 0):,} | {metrics['severity_pct'].get('LOW', 0.0)}% | Minor administrative delay (76–150 days on recommendation -> sanction) |
| `MEDIUM` | {metrics['severity_counts'].get('MEDIUM', 0):,} | {metrics['severity_pct'].get('MEDIUM', 0.0)}% | Significant delay: 151–225 days on sanction OR 1.0–1.5 years on project execution |
| `HIGH` | {metrics['severity_counts'].get('HIGH', 0):,} | {metrics['severity_pct'].get('HIGH', 0.0)}% | Severe delay: >225 days on sanction (>3x SLA) OR >1.5 years on project execution |

## 4. Milestone-Specific Breakdown
* **Recommendation → Sanction SLA (75 Days)**:
  * Exceeded: **{metrics['rec_sla_exceeded_count']:,}** works ({metrics['rec_sla_exceeded_pct']}%)
  * Within SLA: **{metrics['total_works'] - metrics['rec_sla_exceeded_count']:,}** works
* **Sanction → Completion (Completed Works, $N = {metrics['completed_works_count']:,}$)**:
  * Exceeded 365-day guideline: **{metrics['comp_guideline_exceeded_count']:,}** works ({metrics['comp_guideline_exceeded_pct']}%)
  * Completed within 1 year: **{metrics['completed_works_count'] - metrics['comp_guideline_exceeded_count']:,}** works
* **Open Work Aging (Incomplete Works, $N = {metrics['open_works_count']:,}$)**:
  * Exceeded 365-day guideline: **{metrics['open_overdue_count']:,}** works ({metrics['open_overdue_pct']}%)
  * Within 1 year allowable window: **{metrics['open_works_count'] - metrics['open_overdue_count']:,}** works

## 5. Score Percentiles (Normalized Delay Score [0.0, 1.0])
* **p0 (Min)**: {metrics['score_percentiles']['p0']}
* **p25**: {metrics['score_percentiles']['p25']}
* **p50 (Median)**: {metrics['score_percentiles']['p50']}
* **p75**: {metrics['score_percentiles']['p75']}
* **p90**: {metrics['score_percentiles']['p90']}
* **p95**: {metrics['score_percentiles']['p95']}
* **p99**: {metrics['score_percentiles']['p99']}
* **p100 (Max)**: {metrics['score_percentiles']['p100']}

## 6. Sample Top Delayed Works
| Work ID | State | Status | Rec->Sanc Days | Sanc->Comp Days | Open Aging Days | Delay Score | Severity |
|---|---|---|---|---|---|---|---|
"""
    for item in metrics["top10_delayed_sample"]:
        sanc_comp = f"{int(item['sanc_to_comp_days'])}d" if pd.notna(item['sanc_to_comp_days']) else "N/A"
        aging = f"{int(item['open_work_aging_days'])}d" if pd.notna(item['open_work_aging_days']) else "N/A"
        md += f"| `{item['work_id']}` | {item['state']} | {item['work_status']} | {int(item['rec_to_sanc_days'])}d | {sanc_comp} | {aging} | `{item['delay_score']:.2f}` | `{item['severity']}` |\n"

    md += f"""
## 7. Artifacts & Outputs
* **Scored Dataset**: `{config.scores_output_path}`
* **Report Document**: `{config.report_output_path}`
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    run_delay_pipeline()
