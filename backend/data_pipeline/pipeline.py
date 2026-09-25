import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

from .config import (
    ORIGINAL_DATA_DIR,
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
    ACTIVE_DATASETS,
)
from .loaders import (
    discover_raw_files,
    load_csv_with_fallback,
    strip_grand_total_rows,
)
from .lineage import attach_lineage_metadata
from .column_mapping import normalize_column_names
from .work_id import apply_work_id_processing
from .dates import normalize_dates_in_df
from .amounts import normalize_amounts_in_df
from .geography import normalize_geography_in_df
from .cleaners import clean_text_fields_in_df
from .validators import build_dataset_validation_report, validate_cross_dataset_joins

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def process_single_csv(file_info: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    file_path = file_info["path"]
    folder_name = file_info["folder"]
    filename = file_info["filename"]
    dataset_category = file_info["dataset_category"]
    house = file_info["house"]

    logging.info(f"Processing: {folder_name}/{filename} -> Category: {dataset_category}, House: {house}")

    # 1. Load CSV
    df_raw = load_csv_with_fallback(file_path)
    rows_before = len(df_raw)

    # 2. Strip Grand Total footer rows
    df_no_gt, gt_removed = strip_grand_total_rows(df_raw)
    rows_after = len(df_no_gt)

    # 3. Attach lineage metadata
    df_lineage = attach_lineage_metadata(df_no_gt, file_path, dataset_category, house)

    # 4. Normalize column names
    df_cols, col_map = normalize_column_names(df_lineage)

    # 5. Work ID processing
    df_wid, wid_stats = apply_work_id_processing(df_cols)

    # 6. Date normalization
    df_dates, date_stats = normalize_dates_in_df(df_wid)

    # 7. Amount normalization
    df_amounts, amount_stats = normalize_amounts_in_df(df_dates)

    # 8. Geography normalization
    df_geo, geo_stats = normalize_geography_in_df(df_amounts)

    # 9. Categorical text cleaning
    df_clean, clean_stats = clean_text_fields_in_df(df_geo)

    # 10. Build validation report
    val_report = build_dataset_validation_report(
        dataset_name=dataset_category,
        house_name=house,
        source_file=f"{folder_name}/{filename}",
        rows_before=rows_before,
        grand_total_removed=gt_removed,
        rows_after=rows_after,
        df_processed=df_clean,
        work_id_stats=wid_stats,
        date_stats=date_stats,
        amount_stats=amount_stats,
        geo_stats=geo_stats,
        clean_stats=clean_stats,
        col_mapping=col_map,
    )

    return df_clean, val_report

def run_ingestion_pipeline(
    original_dir: Path = ORIGINAL_DATA_DIR,
    processed_dir: Path = PROCESSED_DATA_DIR,
    reports_dir: Path = REPORTS_DIR,
    include_historical: bool = False,
) -> Dict[str, Any]:
    """
    Main entry point for Phase 2 data ingestion & cleaning pipeline.
    Processes active datasets (LokSabha18, RajyaSabha_Sitting), handles missing files gracefully,
    and writes validation reports to data/reports/.
    """
    logging.info("Starting Phase 2 Ingestion & Cleaning Pipeline...")
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Move any legacy processed LokSabha17 output to _historical if present
    legacy_ls17_proc = processed_dir / "LokSabha17"
    if legacy_ls17_proc.exists() and not include_historical:
        hist_dir = processed_dir / "_historical" / "LokSabha17"
        hist_dir.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        if hist_dir.exists():
            shutil.rmtree(hist_dir)
        shutil.move(str(legacy_ls17_proc), str(hist_dir))
        logging.info(f"Archived legacy LokSabha17 processed dataset to: {hist_dir}")

    discovered_files, scope_status = discover_raw_files(original_dir, include_historical=include_historical)
    logging.info(f"Discovered {len(discovered_files)} raw CSV files across target dataset scopes.")

    for folder_name, status_info in scope_status.items():
        if status_info.get("status") == "skipped_no_source_files":
            logging.info(f"{folder_name}: {status_info['message']}")
        elif status_info.get("status") == "excluded_optional_historical":
            logging.info(f"{folder_name}: {status_info['message']}")

    dataset_reports = []
    processed_datasets_map = {}

    for file_info in discovered_files:
        df_proc, val_rep = process_single_csv(file_info)

        folder_name = file_info["folder"]
        dataset_cat = file_info["dataset_category"]

        # Save processed DataFrame as Parquet
        if folder_name in ACTIVE_DATASETS:
            out_folder = processed_dir / folder_name
        else:
            out_folder = processed_dir / "_historical" / folder_name

        out_folder.mkdir(parents=True, exist_ok=True)
        out_parquet_path = out_folder / f"{dataset_cat}.parquet"

        # Convert object columns to string to ensure safe Parquet serialization
        for c in df_proc.columns:
            if df_proc[c].dtype == "object":
                df_proc[c] = df_proc[c].astype(str).replace({"None": None, "nan": None, "NaN": None})

        df_proc.to_parquet(out_parquet_path, index=False)
        logging.info(f"Saved processed dataset: {out_parquet_path} ({len(df_proc):,} rows)")

        dataset_reports.append(val_rep)

        # Store primary dataset (LokSabha18) for cross-dataset join checks
        if folder_name == "LokSabha18":
            processed_datasets_map[dataset_cat] = df_proc

    # Cross-dataset join validation
    join_validation = validate_cross_dataset_joins(processed_datasets_map)

    pipeline_summary_report = {
        "status": "PHASE 2 COMPLETE",
        "scope_status": scope_status,
        "processed_files_count": len(dataset_reports),
        "dataset_validation_reports": dataset_reports,
        "cross_dataset_join_validation": join_validation,
    }

    # Export JSON report
    json_report_path = reports_dir / "data_quality_report.json"
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_summary_report, f, indent=2, default=str)
    logging.info(f"Exported JSON report: {json_report_path}")

    # Export Markdown report
    md_report_path = reports_dir / "data_quality_report.md"
    generate_markdown_report(pipeline_summary_report, md_report_path)
    logging.info(f"Exported Markdown report: {md_report_path}")

    return pipeline_summary_report

def generate_markdown_report(report_data: Dict[str, Any], output_path: Path):
    """Generates human-readable Markdown data-quality report."""
    md = []
    md.append("# Phase 2 — Data Ingestion & Quality Validation Report")
    md.append(f"**Status**: `{report_data['status']}`  ")
    md.append(f"**Active Files Processed**: {report_data['processed_files_count']}  ")
    md.append("\n---\n")

    md.append("## 1. Dataset Scope & Availability Status\n")
    scope = report_data.get("scope_status", {})
    md.append("| Dataset Folder | Scope Category | Status | Details |")
    md.append("|---|---|---|---|")
    for folder, sinfo in scope.items():
        cat = "Active" if sinfo.get("is_active") else "Optional / Historical"
        msg = sinfo.get("message", f"Processed {sinfo.get('file_count', 0)} files")
        md.append(f"| `{folder}` | {cat} | `{sinfo.get('status')}` | {msg} |")

    md.append("\n---\n")
    md.append("## 2. Active Dataset Ingestion Summary\n")
    md.append("| House | Dataset | Source File | Rows Before | Grand Total Removed | Rows After | Valid Work IDs | NA Recs |")
    md.append("|---|---|---|---|---|---|---|---|")

    for d in report_data["dataset_validation_reports"]:
        wid = d.get("work_id_stats", {})
        md.append(
            f"| {d['house_name']} | `{d['dataset_name']}` | `{d['source_file']}` | {d['rows_before']:,} | {d['grand_total_removed']} | {d['rows_after']:,} | {wid.get('valid_work_ids', 0):,} | {wid.get('na_recommendations', 0):,} |"
        )

    md.append("\n---\n")
    md.append("## 3. Cross-Dataset Join Validation (Lok Sabha 18th)\n")

    joins = report_data.get("cross_dataset_join_validation", {})
    if "sanctioned_vs_expenditure" in joins:
        se = joins["sanctioned_vs_expenditure"]
        md.append("### Sanctioned → Expenditure Work ID Match")
        md.append(f"- **Unique Expenditure Work IDs**: {se['unique_expenditure_work_ids']:,}")
        md.append(f"- **Matching Sanctioned Work IDs**: {se['matched_work_ids']:,}")
        md.append(f"- **Unmatched Expenditure Work IDs**: {se['unmatched_expenditure_work_ids']:,}")
        md.append(f"- **Match Percentage**: `{se['expenditure_match_percentage']}%`\n")

    if "completed_vs_sanctioned" in joins:
        cs = joins["completed_vs_sanctioned"]
        md.append("### Completed → Sanctioned Work ID Match")
        md.append(f"- **Unique Completed Work IDs**: {cs['unique_completed_work_ids']:,}")
        md.append(f"- **Matching Sanctioned Work IDs**: {cs['matched_work_ids']:,}")
        md.append(f"- **Unmatched Completed Work IDs**: {cs['unmatched_completed_work_ids']:,}")
        md.append(f"- **Match Percentage**: `{cs['completed_match_percentage']}%`\n")

    if "mp_allocation_vs_sanctioned" in joins:
        ma = joins["mp_allocation_vs_sanctioned"]
        md.append("### MP Allocation → Sanctioned MP Name Match")
        md.append(f"- **Unique Allocated MPs**: {ma['unique_allocated_mps']:,}")
        md.append(f"- **Matching Sanctioned MPs**: {ma['matched_mps']:,}")
        md.append(f"- **Unmatched Allocated MPs**: {ma['unmatched_allocated_mps']:,}")
        md.append(f"- **Match Percentage**: `{ma['mp_match_percentage']}%`\n")

    md.append("\n---\n")
    md.append("## 4. Policy Constants & External Dependencies\n")
    md.append("- **SLA Policy Thresholds**: SLA thresholds are configured as fixed policy constants (75 / 45 / 365 days) according to the finalized Phase 1 specification:")
    md.append("  - Recommendation → Sanction: **75 days**")
    md.append("  - Rejection notification: **45 days**")
    md.append("  - General work completion limit: **365 days**")
    md.append("- **Only Remaining External Dependency**: Authoritative eligible/ineligible MPLADS work-category allowlist.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

if __name__ == "__main__":
    run_ingestion_pipeline()
