from typing import Dict, Any, Optional

class MPParser:
    """Parses MP names, House of Parliament, and Constituency mappings."""

    @staticmethod
    def clean_mp_name(mp_name: Optional[str]) -> Optional[str]:
        if not mp_name or mp_name in ["N/A", "Unknown", "null", "None"]:
            return None
        name = mp_name.replace("Hon'ble", "").replace("Shri", "").replace("Smt.", "").replace("Dr.", "").strip()
        return name.upper() if name else None
