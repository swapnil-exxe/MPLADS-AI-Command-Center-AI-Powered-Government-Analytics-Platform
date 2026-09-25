import pandas as pd
from pathlib import Path

def attach_lineage_metadata(df: pd.DataFrame, file_path: Path, dataset_name: str, house_name: str) -> pd.DataFrame:
    """
    Attaches data lineage metadata to each record in the dataframe.
    
    Columns added:
      - source_file: filename/path
      - source_dataset: dataset classification (e.g. works_sanctioned)
      - source_house: source legislative house (e.g. Lok Sabha)
      - source_row_number: 1-indexed row number from the original CSV
    """
    df = df.copy()
    rel_file = str(file_path.name)
    df["source_file"] = rel_file
    df["source_dataset"] = dataset_name
    df["source_house"] = house_name
    # Preserve 1-indexed original CSV row number (accounting for header row = 1)
    df["source_row_number"] = df.index + 2
    return df
