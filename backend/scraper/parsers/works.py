from typing import Dict, Any, List, Optional
import re

class WorksParser:
    """Parses work recommendation, sanction, and completion records."""

    @staticmethod
    def parse_work_row(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict):
            return None

        work_id = raw.get("WORK_ID") or raw.get("work_id") or raw.get("LETTER_NO") or raw.get("WORK_REC_ID")
        state = raw.get("STATE_NAME") or raw.get("STATE") or raw.get("state")
        district = raw.get("DISTRICT_NAME") or raw.get("DISTRICT") or raw.get("district")

        if not work_id or not state or not district:
            # Fallback ID synthesis from MP + Letter if work_id missing
            if raw.get("MP_NAME") and raw.get("LETTER_NO"):
                clean_mp = re.sub(r"[^A-Za-z0-9]", "", str(raw["MP_NAME"]))
                clean_let = re.sub(r"[^A-Za-z0-9]", "", str(raw["LETTER_NO"]))
                work_id = f"LIVE/{clean_mp}/{clean_let}"
            else:
                return None

        return {
            "work_id": str(work_id).strip(),
            "house": raw.get("HOUSE_NAME") or raw.get("HOUSE_OF_PARLIAMENT") or raw.get("house") or "LOK SABHA",
            "state": str(state).strip(),
            "district": str(district).strip(),
            "constituency": raw.get("CONSTITUENCY_NAME") or raw.get("CONSTITUENCY") or raw.get("constituency"),
            "mp_name": raw.get("MP_NAME") or raw.get("mp_name"),
            "ida": raw.get("IDA_NAME") or raw.get("IMPLEMENTING_AGENCY") or raw.get("ida"),
            "work_category": raw.get("WORK_CATEGORY") or raw.get("CATEGORY") or raw.get("work_category"),
            "work_type": raw.get("WORK_TYPE") or raw.get("work_type"),
            "work_description": raw.get("WORK_DESCRIPTION") or raw.get("WORK_NAME") or raw.get("work_description"),
            "work_status": raw.get("WORK_STATUS") or raw.get("STATUS") or raw.get("work_status") or "SANCTIONED",
            "sanction_amount": raw.get("SANCTIONED_AMOUNT") or raw.get("RECOMMENDED_AMOUNT") or raw.get("sanction_amount"),
            "sanction_date": raw.get("SANCTION_DATE") or raw.get("sanction_date"),
            "recommended_date": raw.get("RECOMMENDATION_DATE") or raw.get("RECOMMENDED_DATE") or raw.get("recommended_date"),
            "completion_date": raw.get("COMPLETION_DATE") or raw.get("completion_date"),
            "amount_disbursed": raw.get("EXPENDITURE_AMT") or raw.get("EXPENDITURE_AMOUNT_") or raw.get("amount_disbursed")
        }
