import hashlib
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional
from scraper.models import NormalizedWorkModel
from scraper.parsers.financials import FinancialsParser
from scraper.parsers.mp import MPParser

class DataNormalizer:
    """
    Maps raw live source dicts to canonical work model.
    Guarantees strict schema adherence and NULL for missing values.
    """

    @staticmethod
    def parse_date_string(date_str: Optional[str]) -> Optional[str]:
        if not date_str or date_str in ["N/A", "null", "None", "", "1970-01-01"]:
            return None
        date_str = str(date_str).strip()
        # Format DD/MM/YYYY or YYYY-MM-DD or DD-MM-YYYY
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(date_str[:10], fmt)
                if 1993 <= dt.year <= 2030:
                    return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None

    @classmethod
    def normalize_work(cls, raw: Dict[str, Any], source_url: str = "https://mplads.mospi.gov.in/digigov/dashboard.html") -> Optional[NormalizedWorkModel]:
        if not isinstance(raw, dict):
            return None

        work_id = raw.get("work_id") or raw.get("WORK_ID") or raw.get("LETTER_NO")
        state = raw.get("state") or raw.get("STATE_NAME") or raw.get("STATE")
        district = raw.get("district") or raw.get("DISTRICT_NAME") or raw.get("DISTRICT")

        if not work_id or not state or not district:
            return None

        work_id_str = str(work_id).strip()
        state_str = str(state).strip().upper()
        district_str = str(district).strip().upper()

        # Parse amounts
        sanc_amt = FinancialsParser.clean_amount(raw.get("sanction_amount") or raw.get("SANCTIONED_AMOUNT") or raw.get("RECOMMENDED_AMOUNT"))
        disb_amt = FinancialsParser.clean_amount(raw.get("amount_disbursed") or raw.get("EXPENDITURE_AMT") or raw.get("EXPENDITURE_AMOUNT_"))

        # Parse dates
        rec_date = cls.parse_date_string(raw.get("recommended_date") or raw.get("RECOMMENDATION_DATE"))
        sanc_date = cls.parse_date_string(raw.get("sanction_date") or raw.get("SANCTION_DATE"))
        comp_date = cls.parse_date_string(raw.get("completion_date") or raw.get("COMPLETION_DATE"))

        # Clean status & house
        status_raw = str(raw.get("work_status") or raw.get("WORK_STATUS") or "SANCTIONED").upper()
        is_completed = "COMPLET" in status_raw or comp_date is not None

        house = str(raw.get("house") or raw.get("HOUSE_NAME") or "LOK SABHA").upper()
        if "RAJYA" in house:
            house = "Rajya Sabha"
        else:
            house = "Lok Sabha"

        mp_name = MPParser.clean_mp_name(raw.get("mp_name") or raw.get("MP_NAME"))

        canonical_dict = {
            "work_id": work_id_str,
            "house": house,
            "state": state_str,
            "district": district_str,
            "constituency": (str(raw.get("constituency") or raw.get("CONSTITUENCY_NAME")).strip().upper() if raw.get("constituency") or raw.get("CONSTITUENCY_NAME") else None),
            "mp_name": mp_name,
            "ida": (str(raw.get("ida") or raw.get("IDA_NAME")).strip() if raw.get("ida") or raw.get("IDA_NAME") else None),
            "work_category": (str(raw.get("work_category") or raw.get("CATEGORY")).strip() if raw.get("work_category") or raw.get("CATEGORY") else None),
            "work_type": (str(raw.get("work_type") or raw.get("WORK_TYPE")).strip() if raw.get("work_type") or raw.get("WORK_TYPE") else None),
            "work_description": (str(raw.get("work_description") or raw.get("WORK_DESCRIPTION") or raw.get("WORK_NAME")).strip() if raw.get("work_description") or raw.get("WORK_DESCRIPTION") or raw.get("WORK_NAME") else None),
            "work_status": status_raw,
            "sanction_amount": sanc_amt,
            "sanction_date": sanc_date,
            "recommended_date": rec_date,
            "completion_date": comp_date,
            "amount_disbursed": disb_amt,
            "is_completed_flag": is_completed,
            "source_dataset": "OFFICIAL_LIVE_ESAKSHI",
            "source_url": source_url
        }

        # Deterministic SHA256 record hash for change detection
        hash_payload = json.dumps(canonical_dict, sort_keys=True, default=str)
        source_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()
        canonical_dict["source_hash"] = source_hash

        return NormalizedWorkModel(**canonical_dict)
