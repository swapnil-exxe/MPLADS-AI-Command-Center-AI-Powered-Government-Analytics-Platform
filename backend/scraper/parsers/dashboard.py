from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

class DashboardParser:
    """Parses macro summary numbers, tile statistics, and HTML content from eSAKSHI dashboard."""

    @staticmethod
    def parse_dashboard_html(html_content: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "lxml")
        metrics = {
            "title": soup.title.string.strip() if soup.title and soup.title.string else "MPLADS Dashboard",
            "stat_cards": {},
            "meta_tags": {}
        }

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            metrics["meta_tags"]["description"] = meta_desc["content"]

        return metrics

    @staticmethod
    def parse_tiles_data_json(json_data: Any, source_url: str = "https://mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesData") -> List[Dict[str, Any]]:
        """Parses /rest/PreLoginDashboardData/getTilesData live dictionary response as Source Summary Metrics."""
        if not isinstance(json_data, dict):
            return []
        
        parsed_metrics = []
        mapping = [
            ("Works Recommended", "RECOMMENDED"),
            ("Works Sanctioned", "SANCTIONED"),
            ("Works Completed", "COMPLETED")
        ]

        for tile_name, status_code in mapping:
            val_arr = json_data.get(tile_name)
            if isinstance(val_arr, list) and len(val_arr) >= 2:
                try:
                    count_val = int(val_arr[0].strip().replace(",", ""))
                except Exception:
                    count_val = 0
                
                amount_str = val_arr[1].strip()
                parsed_metrics.append({
                    "metric_name": tile_name,
                    "metric_value": str(count_val),
                    "formatted_value": amount_str,
                    "status_code": status_code,
                    "source_url": source_url
                })

        return parsed_metrics

    @staticmethod
    def parse_tile_report_json(json_data: Any) -> List[Dict[str, Any]]:
        """Parses /getTilesReportData JSON response array."""
        if not json_data:
            return []
        
        items = json_data if isinstance(json_data, list) else [json_data]
        parsed_records = []

        for row in items:
            if not isinstance(row, dict):
                continue
            parsed_records.append({
                "work_id": row.get("WORK_ID") or row.get("work_id") or row.get("LETTER_NO"),
                "mp_name": row.get("MP_NAME") or row.get("mp_name"),
                "house": row.get("HOUSE_NAME") or row.get("HOUSE_OF_PARLIAMENT") or "LOK SABHA",
                "state": row.get("STATE_NAME") or row.get("STATE"),
                "district": row.get("DISTRICT_NAME") or row.get("DISTRICT") or row.get("CITY_NAME"),
                "constituency": row.get("CONSTITUENCY_NAME") or row.get("CONSTITUENCY"),
                "work_description": row.get("WORK_DESCRIPTION") or row.get("WORK_NAME") or row.get("WORK_TYPE"),
                "work_category": row.get("WORK_CATEGORY") or row.get("CATEGORY"),
                "sanction_amount": row.get("SANCTIONED_AMOUNT") or row.get("RECOMMENDED_AMOUNT") or row.get("ALLOCATED_AMOUNT_"),
                "amount_disbursed": row.get("EXPENDITURE_AMT") or row.get("EXPENDITURE_AMOUNT_"),
                "work_status": row.get("WORK_STATUS") or row.get("STATUS"),
                "recommendation_date": row.get("RECOMMENDATION_DATE") or row.get("RECOMMENDED_DATE"),
                "sanction_date": row.get("SANCTION_DATE"),
                "completion_date": row.get("COMPLETION_DATE"),
                "ida": row.get("IDA_NAME") or row.get("IMPLEMENTING_AGENCY")
            })

        return parsed_records
