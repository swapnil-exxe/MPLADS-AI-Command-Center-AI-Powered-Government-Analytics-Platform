import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
import pandas as pd

from .config import PROCESSED_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_clean_col(df: pd.DataFrame, col_name: str) -> Optional[pd.Series]:
    """Helper to extract a column if present, handling positional lineage column names."""
    if col_name in df.columns:
        return df[col_name]
    return None

def normalize_constituency_column(df: pd.DataFrame, default_house: str = "Lok Sabha") -> pd.DataFrame:
    """Normalizes 'constituency' or 'elected' into 'constituency_or_term', and populates 'house'."""
    df = df.copy()
    if "constituency" in df.columns:
        df["constituency_or_term"] = df["constituency"]
    elif "elected" in df.columns:
        df["constituency_or_term"] = df["elected"]
    else:
        df["constituency_or_term"] = None

    if "house" not in df.columns or df["house"].isna().all():
        if "source_house" in df.columns and df["source_house"].notna().any():
            df["house"] = df["source_house"]
        else:
            df["house"] = default_house
    return df

def build_canonical_layer(
    processed_dir: Path = PROCESSED_DATA_DIR,
    active_folders: Tuple[str, ...] = ("LokSabha18", "RajyaSabha_Sitting")
) -> Dict[str, pd.DataFrame]:
    """
    Constructs the canonical entity data layer centered around WORK.
    Combines active Lok Sabha and Rajya Sabha datasets.
    
    Returns dictionary containing:
      - canonical_works: Work-level master dataframe
      - canonical_expenditures: Transaction-level expenditure dataframe
      - canonical_mp_allocations: MP allocation limits dataframe
      - canonical_calamity: Calamity consent dataframe
    """
    logging.info("Building Canonical Data Layer from active Phase 2 outputs...")
    
    sanc_dfs = []
    recom_dfs = []
    comp_dfs = []
    exp_dfs = []
    mp_dfs = []
    calamity_dfs = []
    
    for folder_name in active_folders:
        folder_path = processed_dir / folder_name
        if not folder_path.exists():
            logging.info(f"Directory {folder_path} does not exist. Skipping.")
            continue
            
        house_name = "Rajya Sabha" if "rajya" in folder_name.lower() else "Lok Sabha"

        sanc_p = folder_path / "works_sanctioned.parquet"
        if sanc_p.exists():
            df_s = pd.read_parquet(sanc_p)
            df_s = normalize_constituency_column(df_s, default_house=house_name)
            sanc_dfs.append(df_s)
            
        recom_p = folder_path / "works_recommended.parquet"
        if recom_p.exists():
            df_r = pd.read_parquet(recom_p)
            df_r = normalize_constituency_column(df_r, default_house=house_name)
            recom_dfs.append(df_r)
            
        comp_p = folder_path / "works_completed.parquet"
        if comp_p.exists():
            df_c = pd.read_parquet(comp_p)
            df_c = normalize_constituency_column(df_c, default_house=house_name)
            comp_dfs.append(df_c)
            
        exp_p = folder_path / "expenditures.parquet"
        if exp_p.exists():
            df_e = pd.read_parquet(exp_p)
            df_e = normalize_constituency_column(df_e, default_house=house_name)
            exp_dfs.append(df_e)
            
        mp_p = folder_path / "mp_allocations.parquet"
        if mp_p.exists():
            df_m = pd.read_parquet(mp_p)
            df_m = normalize_constituency_column(df_m, default_house=house_name)
            mp_dfs.append(df_m)
            
        cal_p = folder_path / "calamity.parquet"
        if cal_p.exists():
            df_cal = pd.read_parquet(cal_p)
            calamity_dfs.append(df_cal)
            
    df_sanc_all = pd.concat(sanc_dfs, ignore_index=True) if sanc_dfs else pd.DataFrame()
    df_recom_all = pd.concat(recom_dfs, ignore_index=True) if recom_dfs else pd.DataFrame()
    df_comp_all = pd.concat(comp_dfs, ignore_index=True) if comp_dfs else pd.DataFrame()
    df_exp_all = pd.concat(exp_dfs, ignore_index=True) if exp_dfs else pd.DataFrame()
    df_mp_all = pd.concat(mp_dfs, ignore_index=True) if mp_dfs else pd.DataFrame()
    df_calamity_all = pd.concat(calamity_dfs, ignore_index=True) if calamity_dfs else pd.DataFrame()
    
    # Construct Canonical Works Master Table centered on Sanctioned Works
    # Left join completion dates/images from Works Completed
    df_comp_subset = df_comp_all[["work_id", "completion_date", "amount_disbursed", "image_url"]].drop_duplicates(subset=["work_id"])
    canonical_works = pd.merge(df_sanc_all, df_comp_subset, on="work_id", how="left", suffixes=("", "_comp"))
    
    # Reconcile amount_disbursed with actual line-item expenditure vouchers from df_exp_all
    # Completed works retain their certificate amount_disbursed; ongoing works populate from voucher sum.
    # Works with zero vouchers legitimately retain NaN/None.
    if not df_exp_all.empty and "work_id" in df_exp_all.columns:
        exp_valid = df_exp_all[df_exp_all["work_id"].notna()].copy()
        exp_valid["exp_amt"] = pd.to_numeric(exp_valid["fund_disbursed_amount"], errors="coerce").fillna(0.0)
        exp_totals = exp_valid.groupby("work_id")["exp_amt"].sum().reset_index().rename(
            columns={"exp_amt": "exp_total_disbursed"}
        )
        canonical_works = pd.merge(canonical_works, exp_totals, on="work_id", how="left")
        canonical_works["amount_disbursed"] = canonical_works["amount_disbursed"].combine_first(canonical_works["exp_total_disbursed"])
        canonical_works.drop(columns=["exp_total_disbursed"], inplace=True)
    
    # Mark is_completed_flag
    canonical_works["is_completed_flag"] = canonical_works["completion_date"].notna()
    
    logging.info(f"Canonical Works: {len(canonical_works):,} rows across {canonical_works['work_id'].nunique():,} unique Work IDs.")
    logging.info(f"Canonical Expenditures: {len(df_exp_all):,} transaction rows.")
    logging.info(f"Canonical MP Allocations: {len(df_mp_all):,} rows.")
    logging.info(f"Canonical Calamity Consents: {len(df_calamity_all):,} rows.")
    
    return {
        "canonical_works": canonical_works,
        "canonical_expenditures": df_exp_all,
        "canonical_mp_allocations": df_mp_all,
        "canonical_calamity": df_calamity_all,
        "raw_recommended": df_recom_all
    }
