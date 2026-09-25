import pytest
import pandas as pd
from pathlib import Path

from data_pipeline.work_id import extract_and_normalize_work_id, apply_work_id_processing
from data_pipeline.loaders import strip_grand_total_rows
from data_pipeline.amounts import parse_monetary_amount, normalize_amounts_in_df
from data_pipeline.dates import parse_date_string, normalize_dates_in_df
from data_pipeline.geography import extract_district_from_ida, normalize_geography_in_df
from data_pipeline.lineage import attach_lineage_metadata

def test_work_id_regex_and_tab_cleaning():
    raw_val = "WS/\t MP620/2024-2025/133166-Construction of buildings for community cultural activities"
    wid, tmpl, is_na = extract_and_normalize_work_id(raw_val)
    assert wid == "WS/MP620/2024-2025/133166"
    assert tmpl == "Construction of buildings for community cultural activities"
    assert is_na is False

def test_grand_total_row_removal():
    data = {
        "Sr. No.": ["1", "2", "Grand Total"],
        "Work": ["WS/MP1/2024-2025/1", "WS/MP1/2024-2025/2", "Total"],
        "Sanction Amount ( ₹ )": ["1000", "2000", "3000"]
    }
    df = pd.DataFrame(data)
    df_clean, removed_count = strip_grand_total_rows(df)
    assert removed_count == 1
    assert len(df_clean) == 2
    assert "Grand Total" not in df_clean["Sr. No."].values

def test_amount_parsing_indian_format():
    raw_val = "41,76,59,96,002.88"
    parsed = parse_monetary_amount(raw_val)
    assert parsed == 41765996002.88

def test_date_parsing_standard_format():
    raw_val = "21-Aug-2026"
    parsed = parse_date_string(raw_val)
    assert parsed == "2026-08-21"

def test_district_extraction_from_ida():
    raw_ida = "GHAZIABAD(DISTRICT MAGISTRAE GHAZIABAD_IDA)"
    district = extract_district_from_ida(raw_ida)
    assert district == "GHAZIABAD"

def test_na_recommendation_handling():
    raw_val = "NA-Construction of Community Hall"
    wid, tmpl, is_na = extract_and_normalize_work_id(raw_val)
    assert wid is None
    assert tmpl == "Construction of Community Hall"
    assert is_na is True

def test_provenance_and_lineage_metadata():
    df = pd.DataFrame({"col1": ["a", "b"]})
    df_lin = attach_lineage_metadata(df, Path("data/original/LokSabha18/test.csv"), "works_sanctioned", "Lok Sabha")
    assert "source_file" in df_lin.columns
    assert "source_dataset" in df_lin.columns
    assert "source_house" in df_lin.columns
    assert "source_row_number" in df_lin.columns
    assert df_lin["source_file"].iloc[0] == "test.csv"
    assert df_lin["source_dataset"].iloc[0] == "works_sanctioned"
    assert df_lin["source_house"].iloc[0] == "Lok Sabha"
    assert list(df_lin["source_row_number"]) == [2, 3]

from data_pipeline.loaders import discover_raw_files

def test_active_and_historical_scope_discovery(tmp_path):
    active_dir = tmp_path / "LokSabha18"
    active_dir.mkdir()
    (active_dir / "sample.csv").write_text("Sr. No.,Work\n1,WS/MP1/2024-2025/1\n")
    
    empty_rs = tmp_path / "RajyaSabha_Sitting"
    empty_rs.mkdir()
    
    hist_dir = tmp_path / "LokSabha17"
    hist_dir.mkdir()
    (hist_dir / "old.csv").write_text("Sr. No.,Work\n1,WS/MP1/2020-2021/1\n")

    files, status = discover_raw_files(base_dir=tmp_path, include_historical=False)
    assert len(files) == 1
    assert files[0]["filename"] == "sample.csv"
    assert status["LokSabha18"]["status"] == "processed"
    assert status["RajyaSabha_Sitting"]["status"] == "skipped_no_source_files"
    assert status["LokSabha17"]["status"] == "excluded_optional_historical"

def test_empty_dataset_directory_handling(tmp_path):
    empty_dir = tmp_path / "RajyaSabha_Sitting"
    empty_dir.mkdir()
    files, status = discover_raw_files(base_dir=tmp_path, include_historical=False)
    assert len(files) == 0
    assert status["RajyaSabha_Sitting"]["status"] == "skipped_no_source_files"
    assert "Skipped without error" in status["RajyaSabha_Sitting"]["message"]
