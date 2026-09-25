from typing import Dict, Any, Optional

class FinancialsParser:
    """Parses expenditure amounts, sanctioned limits, and tranche data."""

    @staticmethod
    def clean_amount(val: Any) -> Optional[float]:
        if val is None or val == "" or val == "N/A" or val == "null":
            return None
        try:
            cleaned = str(val).replace(",", "").replace("₹", "").replace("Cr", "").strip()
            num = float(cleaned)
            return num if num >= 0 else None
        except (ValueError, TypeError):
            return None
