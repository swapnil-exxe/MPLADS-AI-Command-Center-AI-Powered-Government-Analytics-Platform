import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

FEATURE_REGISTRY_ENTRIES = [
    # Model 1 Features
    {
        "feature_name": "sanction_amount_log",
        "description": "Log1p transformed sanction amount to handle heavy right skew",
        "source_dataset": "works_sanctioned",
        "source_columns": ["sanction_amount"],
        "unit_of_analysis": "work",
        "formula": "log(1 + sanction_amount)",
        "data_type": "float64",
        "null_handling": "Fill with 0.0",
        "normalization": "Log scale",
        "used_by": "Model 1 (Cost Anomaly)",
        "leakage_risk": "None (Sanction-time feature)",
        "status": "INCLUDED"
    },
    {
        "feature_name": "peer_iqr_deviation",
        "description": "Robust IQR deviation of sanction amount vs fallback peer group median",
        "source_dataset": "works_sanctioned",
        "source_columns": ["sanction_amount", "state", "work_type_template"],
        "unit_of_analysis": "work",
        "formula": "(sanction_amount - peer_median) / (peer_iqr / 1.349)",
        "data_type": "float64",
        "null_handling": "Computed using fallback peer hierarchy (State->National)",
        "normalization": "Gaussian-equivalent robust scaling",
        "used_by": "Model 1 (Cost Anomaly)",
        "leakage_risk": "None (Sanction-time feature)",
        "status": "INCLUDED"
    },
    {
        "feature_name": "cost_ratio_vs_peer_median",
        "description": "Ratio of sanctioned cost vs peer group median cost",
        "source_dataset": "works_sanctioned",
        "source_columns": ["sanction_amount", "state", "work_type_template"],
        "unit_of_analysis": "work",
        "formula": "sanction_amount / peer_median_amount",
        "data_type": "float64",
        "null_handling": "Computed using fallback peer hierarchy",
        "normalization": "Ratio scale",
        "used_by": "Model 1 (Cost Anomaly)",
        "leakage_risk": "None (Sanction-time feature)",
        "status": "INCLUDED"
    },
    {
        "feature_name": "is_data_quality_exception",
        "description": "Boolean flag for sanction amount below 1,000 INR decimal floor exception",
        "source_dataset": "works_sanctioned",
        "source_columns": ["sanction_amount"],
        "unit_of_analysis": "work",
        "formula": "0 < sanction_amount < 1000",
        "data_type": "bool",
        "null_handling": "False if null",
        "normalization": "Binary flag",
        "used_by": "Model 1 (Cost Anomaly) & DQ Routing",
        "leakage_risk": "None",
        "status": "INCLUDED"
    },

    # Model 2 Candidate Pair Features
    {
        "feature_name": "days_diff",
        "description": "Absolute difference in sanction date between candidate duplicate pair",
        "source_dataset": "works_sanctioned",
        "source_columns": ["sanction_date"],
        "unit_of_analysis": "work_pair",
        "formula": "abs(sanction_date_1 - sanction_date_2).days",
        "data_type": "int64",
        "null_handling": "Blocked within 90-day window",
        "normalization": "Days scale",
        "used_by": "Model 2 (Duplicate Detection)",
        "leakage_risk": "None",
        "status": "INCLUDED"
    },
    {
        "feature_name": "amount_ratio",
        "description": "Ratio of min to max sanction amount between candidate pair",
        "source_dataset": "works_sanctioned",
        "source_columns": ["sanction_amount"],
        "unit_of_analysis": "work_pair",
        "formula": "min(amt1, amt2) / max(amt1, amt2)",
        "data_type": "float64",
        "null_handling": "0.0 if max_amt is 0",
        "normalization": "Bounded 0 to 1",
        "used_by": "Model 2 (Duplicate Detection)",
        "leakage_risk": "None",
        "status": "INCLUDED"
    },

    # Model 3 Expenditure Features
    {
        "feature_name": "utilization_ratio",
        "description": "Ratio of total expenditure disbursed vs sanction amount, capped at 1.00",
        "source_dataset": "expenditures, works_sanctioned",
        "source_columns": ["fund_disbursed_amount", "sanction_amount"],
        "unit_of_analysis": "work",
        "formula": "min(1.00, sum(fund_disbursed) / sanction_amount)",
        "data_type": "float64",
        "null_handling": "0.0 if no expenditure or 0 sanction",
        "normalization": "Bounded 0 to 1",
        "used_by": "Model 3 (Expenditure Anomaly) & Logic 2",
        "leakage_risk": "Post-sanction (Model 3 only)",
        "status": "INCLUDED"
    },
    {
        "feature_name": "payment_concentration_hhi",
        "description": "Herfindahl Index of payment tranche amounts within a work",
        "source_dataset": "expenditures",
        "source_columns": ["fund_disbursed_amount"],
        "unit_of_analysis": "work",
        "formula": "sum((tranche_amount / total_disbursed)^2)",
        "data_type": "float64",
        "null_handling": "0.0 if no disbursement",
        "normalization": "Bounded 0 to 1",
        "used_by": "Model 3 (Expenditure Anomaly)",
        "leakage_risk": "Post-sanction (Model 3 only)",
        "status": "INCLUDED"
    },

    # Model 4 Forecasting Features
    {
        "feature_name": "total_disbursed_amount_monthly",
        "description": "Monthly aggregate expenditure sum for State x Month time series",
        "source_dataset": "expenditures",
        "source_columns": ["fund_disbursed_amount", "expenditure_date", "state"],
        "unit_of_analysis": "state_month",
        "formula": "sum(fund_disbursed_amount) per State and Month",
        "data_type": "float64",
        "null_handling": "Retained as 0.0 for true zero-spend months",
        "normalization": "INR Currency scale",
        "used_by": "Model 4 (Expenditure Forecasting)",
        "leakage_risk": "None (Historical time series)",
        "status": "INCLUDED"
    },

    # Logic & Vendor Features
    {
        "feature_name": "rec_to_sanc_sla_exceeded_flag",
        "description": "Boolean flag if recommendation to sanction duration exceeds 75 days policy SLA",
        "source_dataset": "works_sanctioned",
        "source_columns": ["recommended_date", "sanction_date"],
        "unit_of_analysis": "work",
        "formula": "rec_to_sanc_days > 75",
        "data_type": "bool",
        "null_handling": "False if missing dates",
        "normalization": "Binary flag",
        "used_by": "Logic 1 (Delay & SLA Logic)",
        "leakage_risk": "None",
        "status": "INCLUDED"
    },
    {
        "feature_name": "entitlement_exceeded_flag",
        "description": "Boolean flag if MP cumulative sanctioned total exceeds allocated limit",
        "source_dataset": "mp_allocations, works_sanctioned",
        "source_columns": ["allocated_amount", "sanction_amount"],
        "unit_of_analysis": "mp",
        "formula": "sum(sanction_amount) > allocated_amount",
        "data_type": "bool",
        "null_handling": "False if missing",
        "normalization": "Binary flag",
        "used_by": "Logic 3 (Compliance Rule Engine)",
        "leakage_risk": "None",
        "status": "INCLUDED"
    },
    {
        "feature_name": "ida_vendor_hhi",
        "description": "Herfindahl Index of vendor disbursement concentration within a district/IDA",
        "source_dataset": "expenditures",
        "source_columns": ["fund_disbursed_amount", "vendor_name", "ida"],
        "unit_of_analysis": "ida",
        "formula": "sum((vendor_ida_disbursed / ida_total_disbursed)^2)",
        "data_type": "float64",
        "null_handling": "0.0 if no spend",
        "normalization": "Bounded 0 to 1",
        "used_by": "Vendor-Agency Risk Analyzer",
        "leakage_risk": "None",
        "status": "INCLUDED"
    }
]

REJECTED_FEATURE_ENTRIES = [
    {
        "candidate_feature": "physical_progress_percentage",
        "status": "REJECTED",
        "reason_rejected": "No numeric physical-progress percentage field exists in any raw or processed MPLADS dataset."
    },
    {
        "candidate_feature": "intraday_payment_velocity",
        "status": "REJECTED",
        "reason_rejected": "Expenditure timestamps supply transaction dates only, not intraday time of day."
    },
    {
        "candidate_feature": "literal_cost_overrun_amount",
        "status": "REJECTED",
        "reason_rejected": "Disbursement is strictly capped at sanctioned ceiling (utilization <= 1.00). Replaced by Utilization Gap and Re-sanction rules."
    },
    {
        "candidate_feature": "sc_st_beneficiary_earmark_pct",
        "status": "REJECTED",
        "reason_rejected": "No caste or beneficiary category field exists in raw CSV datasets."
    }
]

def generate_feature_quality_report(
    feature_tables: Dict[str, pd.DataFrame],
    output_json_path: Path,
    output_md_path: Path
):
    """
    Computes summary statistics, null counts, skewness, and redundancy diagnostics across feature tables,
    and exports feature registry & quality reports in JSON and Markdown formats.
    """
    logging.info("Generating Feature Quality & Diagnostics Report...")
    
    table_summaries = {}
    
    for tname, df in feature_tables.items():
        if df is None or df.empty:
            continue
            
        num_cols = df.select_dtypes(include=[np.number]).columns
        num_stats = {}
        for c in num_cols:
            s = df[c].dropna()
            num_stats[c] = {
                "count": len(s),
                "null_count": int(df[c].isna().sum()),
                "null_pct": round(float(df[c].isna().sum() / len(df) * 100), 2),
                "min": float(s.min()) if not s.empty else None,
                "max": float(s.max()) if not s.empty else None,
                "mean": float(s.mean()) if not s.empty else None,
                "median": float(s.median()) if not s.empty else None,
                "std": float(s.std()) if not s.empty else None,
                "skew": float(s.skew()) if len(s) > 2 else None,
            }
            
        table_summaries[tname] = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "numeric_feature_diagnostics": num_stats
        }
        
    full_report = {
        "status": "PHASE 3 COMPLETE",
        "feature_registry": FEATURE_REGISTRY_ENTRIES,
        "rejected_features": REJECTED_FEATURE_ENTRIES,
        "feature_quality_diagnostics": table_summaries
    }
    
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, default=str)
        
    # Write Markdown Report
    md = []
    md.append("# Phase 3 — Feature Engineering & Feature Quality Report")
    md.append("**Status**: `PHASE 3 COMPLETE`  ")
    md.append("\n---\n")
    
    md.append("## 1. Feature Registry & Model Mapping\n")
    md.append("| Feature Name | Used By | Unit of Analysis | Formula / Derivation | Leakage Control | Status |")
    md.append("|---|---|---|---|---|---|")
    for f in FEATURE_REGISTRY_ENTRIES:
        md.append(f"| `{f['feature_name']}` | {f['used_by']} | `{f['unit_of_analysis']}` | `{f['formula']}` | {f['leakage_risk']} | `{f['status']}` |")
        
    md.append("\n---\n")
    md.append("## 2. Explicitly Rejected Candidate Features\n")
    md.append("| Candidate Feature | Status | Reason Rejected |")
    md.append("|---|---|---|")
    for r in REJECTED_FEATURE_ENTRIES:
        md.append(f"| `{r['candidate_feature']}` | `{r['status']}` | {r['reason_rejected']} |")
        
    md.append("\n---\n")
    md.append("## 3. Feature Coverage & Quality Diagnostics Summary\n")
    for tname, tinfo in table_summaries.items():
        md.append(f"### Table: `{tname}` ({tinfo['total_records']:,} rows, {tinfo['total_columns']} columns)")
        md.append("| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |")
        md.append("|---|---|---|---|---|---|---|")
        for fname, d in tinfo["numeric_feature_diagnostics"].items():
            min_str = f"₹{d['min']:,.2f}" if abs(d['min'] or 0) > 10 else f"{d['min']:.2f}"
            max_str = f"₹{d['max']:,.2f}" if abs(d['max'] or 0) > 10 else f"{d['max']:.2f}"
            med_str = f"₹{d['median']:,.2f}" if abs(d['median'] or 0) > 10 else f"{d['median']:.2f}"
            skew_str = f"{d['skew']:.2f}" if d['skew'] is not None else "N/A"
            md.append(f"| `{fname}` | {d['count']:,} | {d['null_pct']}% | {min_str} | {max_str} | {med_str} | {skew_str} |")
        md.append("\n")
        
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
        
    logging.info(f"Exported feature registry and quality report to {output_json_path} and {output_md_path}")
