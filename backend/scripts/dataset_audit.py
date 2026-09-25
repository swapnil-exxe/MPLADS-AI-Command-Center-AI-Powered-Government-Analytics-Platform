import os
import sys
import chardet
import json
import pandas as pd
import numpy as np
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
dataset_dir = root_dir / "dataset"

def run_dataset_audit():
    print("======================================================================")
    print("PHASE 1 & 2: SCANNING ALL RAW CSV FILES & DATA INTEGRITY AUDIT")
    print(f"Directory: {dataset_dir}")
    print("======================================================================")

    csv_files = sorted(list(dataset_dir.rglob("*.csv")))
    print(f"Total Raw CSV Files Found: {len(csv_files)}\n")

    report_data = []
    total_raw_rows = 0
    total_missing_values = 0
    total_duplicate_rows = 0

    for f in csv_files:
        rel_path = str(f.relative_to(dataset_dir))
        source_group = rel_path.split("/")[0]
        file_size_mb = f.stat().st_size / (1024 * 1024)

        # Encoding detection
        with open(f, "rb") as fp:
            raw_sample = fp.read(10000)
            enc = chardet.detect(raw_sample)["encoding"] or "utf-8"

        try:
            df = pd.read_csv(f, encoding=enc, low_memory=False)
            rows = len(df)
            cols = len(df.columns)
            total_raw_rows += rows
            
            missing_count = int(df.isnull().sum().sum())
            total_missing_values += missing_count

            dup_count = int(df.duplicated().sum())
            total_duplicate_rows += dup_count

            # Detect work id column if applicable
            work_id_col = None
            for c in df.columns:
                if c in ["Work ID", "Work", "WORK"]:
                    work_id_col = c
                    break

            unique_work_ids = df[work_id_col].nunique() if work_id_col else 0

            report_data.append({
                "file": rel_path,
                "source_group": source_group,
                "file_size_mb": round(file_size_mb, 2),
                "encoding": enc,
                "total_rows": rows,
                "total_cols": cols,
                "duplicate_rows": dup_count,
                "missing_values": missing_count,
                "work_id_col": work_id_col,
                "unique_work_ids": unique_work_ids,
                "columns": list(df.columns)
            })

            print(f"[{source_group}] {f.name}: {rows:,} rows | {cols} cols | {file_size_mb:.2f} MB | Encoding: {enc}")

        except Exception as e:
            print(f"[ERROR] Failed to read {rel_path}: {e}")

    # Output Data Quality Summary Report
    summary = {
        "raw_files_found": len(csv_files),
        "total_raw_rows": total_raw_rows,
        "total_duplicate_rows": total_duplicate_rows,
        "total_missing_values": total_missing_values,
        "file_details": report_data
    }

    report_path = root_dir / "data" / "reports" / "data_quality_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)

    print("\n======================================================================")
    print(f"RAW FILES FOUND: {len(csv_files)}")
    print(f"TOTAL RAW ROWS: {total_raw_rows:,}")
    print(f"TOTAL DUPLICATE ROWS: {total_duplicate_rows:,}")
    print(f"TOTAL MISSING VALUES: {total_missing_values:,}")
    print(f"Data Quality Report saved to: {report_path}")
    print("======================================================================")

if __name__ == "__main__":
    run_dataset_audit()
