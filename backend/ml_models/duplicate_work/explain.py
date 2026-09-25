import pandas as pd

def generate_duplicate_explanation(row: pd.Series) -> str:
    """
    Generates transparent, human-readable, auditable explanation for candidate pairs.
    NEVER declares fraud or confirmed duplication.
    """
    sem = float(row.get("semantic_similarity", 0.0))
    dup_score = float(row.get("duplicate_score", 0.0))
    conf = float(row.get("confidence", 1.0))
    days = int(row.get("days_diff", 0))
    amt1 = float(row.get("sanction_amount_1", 0.0))
    amt2 = float(row.get("sanction_amount_2", 0.0))
    diff = float(row.get("amount_diff_abs", 0.0))
    ratio = float(row.get("amount_ratio", 1.0))
    dist = str(row.get("district", "UNKNOWN"))
    tmpl = str(row.get("work_type_template", "UNKNOWN"))
    same_mp = "Yes" if row.get("is_same_mp", False) else "No"
    same_const = "Yes" if row.get("is_same_constituency", False) else "No"
    
    desc1 = str(row.get("work_description_1", ""))[:120]
    desc2 = str(row.get("work_description_2", ""))[:120]
    
    flags = []
    if row.get("is_short_description", False):
        flags.append("Short description")
    if row.get("is_generic_description", False):
        flags.append("Generic description")
    flag_str = f" | Flags: {', '.join(flags)}" if flags else ""
    
    return (
        f"POTENTIAL DUPLICATE — REQUIRES REVIEW: "
        f"Semantic similarity {sem:.2f}, sanction amounts ₹{amt1:,.2f} vs ₹{amt2:,.2f} (ratio {ratio:.2f}), "
        f"sanction dates {days}d apart in {dist} ({tmpl}). "
        f"Same MP: {same_mp} | Same Constituency: {same_const}. "
        f"Confidence: {conf:.2f}{flag_str}. Overall score: {dup_score:.2f}."
    )

def add_explanations_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """Adds explanation column to scored dataframe."""
    df = df.copy()
    df["explanation"] = [generate_duplicate_explanation(row) for _, row in df.iterrows()]
    return df
