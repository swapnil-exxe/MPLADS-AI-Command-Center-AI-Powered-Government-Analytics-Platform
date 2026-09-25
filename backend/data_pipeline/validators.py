from typing import Dict, Any, List
import pandas as pd

def build_dataset_validation_report(
    dataset_name: str,
    house_name: str,
    source_file: str,
    rows_before: int,
    grand_total_removed: int,
    rows_after: int,
    df_processed: pd.DataFrame,
    work_id_stats: Dict[str, Any],
    date_stats: Dict[str, Any],
    amount_stats: Dict[str, Any],
    geo_stats: Dict[str, Any],
    clean_stats: Dict[str, Any],
    col_mapping: Dict[str, str]
) -> Dict[str, Any]:
    """
    Builds a comprehensive validation report dictionary for a single dataset.
    """
    null_counts = {}
    for col in df_processed.columns:
        s = df_processed[col].isna().sum()
        null_counts[col] = int(s.sum()) if hasattr(s, "sum") else int(s)
    
    report = {
        "dataset_name": dataset_name,
        "house_name": house_name,
        "source_file": source_file,
        "rows_before": rows_before,
        "grand_total_removed": grand_total_removed,
        "rows_after": rows_after,
        "column_count": len(df_processed.columns),
        "columns": list(df_processed.columns),
        "source_to_canonical_mapping": col_mapping,
        "null_counts_by_column": null_counts,
        "work_id_stats": work_id_stats,
        "date_stats": date_stats,
        "amount_stats": amount_stats,
        "geography_stats": geo_stats,
        "category_status_stats": clean_stats,
    }
    return report

def validate_cross_dataset_joins(datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Performs cross-dataset relationship checks across processed datasets.
    Checks:
      1. Sanctioned -> Expenditure Work ID match
      2. Completed -> Sanctioned Work ID match
      3. MP Allocation -> Sanctioned MP Name match
    """
    results = {}
    
    # 1. Sanctioned vs Expenditure
    sanc_df = datasets.get("works_sanctioned")
    exp_df = datasets.get("expenditures")
    comp_df = datasets.get("works_completed")
    mp_df = datasets.get("mp_allocations")
    
    if sanc_df is not None and exp_df is not None:
        sanc_wids = set(sanc_df["work_id"].dropna().unique())
        exp_wids = set(exp_df["work_id"].dropna().unique())
        matched_exp = exp_wids.intersection(sanc_wids)
        
        results["sanctioned_vs_expenditure"] = {
            "unique_expenditure_work_ids": len(exp_wids),
            "unique_sanctioned_work_ids": len(sanc_wids),
            "matched_work_ids": len(matched_exp),
            "unmatched_expenditure_work_ids": len(exp_wids - sanc_wids),
            "expenditure_match_percentage": round(len(matched_exp) / len(exp_wids) * 100, 2) if exp_wids else 0.0,
        }
        
    # 2. Completed vs Sanctioned
    if comp_df is not None and sanc_df is not None:
        comp_wids = set(comp_df["work_id"].dropna().unique())
        sanc_wids = set(sanc_df["work_id"].dropna().unique())
        matched_comp = comp_wids.intersection(sanc_wids)
        
        results["completed_vs_sanctioned"] = {
            "unique_completed_work_ids": len(comp_wids),
            "matched_work_ids": len(matched_comp),
            "unmatched_completed_work_ids": len(comp_wids - sanc_wids),
            "completed_match_percentage": round(len(matched_comp) / len(comp_wids) * 100, 2) if comp_wids else 0.0,
        }
        
    # 3. MP Allocation vs Sanctioned
    if mp_df is not None and sanc_df is not None:
        alloc_mps = set(mp_df["mp_name"].dropna().str.strip().unique())
        sanc_mps = set(sanc_df["mp_name"].dropna().str.strip().unique())
        matched_mps = alloc_mps.intersection(sanc_mps)
        
        results["mp_allocation_vs_sanctioned"] = {
            "unique_allocated_mps": len(alloc_mps),
            "unique_sanctioned_mps": len(sanc_mps),
            "matched_mps": len(matched_mps),
            "unmatched_allocated_mps": len(alloc_mps - sanc_mps),
            "mp_match_percentage": round(len(matched_mps) / len(alloc_mps) * 100, 2) if alloc_mps else 0.0,
        }
        
    return results
