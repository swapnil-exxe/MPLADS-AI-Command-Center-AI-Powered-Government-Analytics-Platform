import logging
from typing import List, Dict, Any, Tuple, Optional
from scraper.client import ResilientScraperClient
from scraper.config import scraper_settings
from scraper.snapshots import SnapshotManager
from scraper.parsers.dashboard import DashboardParser
from scraper.parsers.works import WorksParser

logger = logging.getLogger("scraper.discovery")

class EndpointDiscovery:
    """
    Discovers and fetches public eSAKSHI dashboard data and REST endpoints
    without attempting private/authenticated access.
    """

    def __init__(self, client: Optional[ResilientScraperClient] = None):
        self.client = client or ResilientScraperClient()

    def discover_and_harvest(self, db: Optional[Any] = None) -> Tuple[List[Dict[str, Any]], str, int, str]:
        """
        Executes discovery workflow:
        1. Harvests live HTML from target dashboard.html
        2. Queries public REST tiles endpoint `/rest/PreLoginDashboardData/getTilesData`
        3. Returns combined raw extracted rows, target URL, HTTP status code, and source type.
        """
        target_url = scraper_settings.TARGET_URL
        logger.info(f"Initiating endpoint discovery for {target_url}")
        source_type = "LIVE_DASHBOARD_SUMMARY"

        # Step 1: Harvest main HTML page
        html_res = self.client.fetch_url(target_url)
        status_code = html_res.get("status_code", 500)
        html_content = html_res.get("content", "")

        # Save HTML snapshot
        SnapshotManager.create_snapshot(target_url, html_content, status_code, db=db)

        raw_rows = []

        # Step 2: Query public getTilesData endpoint
        tiles_url = f"{scraper_settings.BASE_DOMAIN}/rest/PreLoginDashboardData/getTilesData"
        tiles_res = self.client.fetch_post_json(tiles_url, {"uname": "0,0,0,2"})
        if tiles_res.get("status_code") == 200 and tiles_res.get("data"):
            SnapshotManager.create_snapshot(tiles_url, tiles_res["data"], 200, db=db)
            parsed_tiles = DashboardParser.parse_tiles_data_json(tiles_res["data"], source_url=tiles_url)
            raw_rows.extend(parsed_tiles)

        # Step 3: Query public REST report endpoints
        rest_url = f"{scraper_settings.BASE_DOMAIN}/rest/PreLoginDashboardData/getTilesReportData"
        payloads = [
            {"house": "LOK", "tenure": "18"},
            {"house": "RAJYA", "tenure": "0"}
        ]

        for p in payloads:
            rest_res = self.client.fetch_post_json(rest_url, p)
            if rest_res.get("status_code") == 200 and rest_res.get("data"):
                # Save REST JSON snapshot
                SnapshotManager.create_snapshot(rest_url, rest_res["data"], 200, db=db)
                parsed = DashboardParser.parse_tile_report_json(rest_res["data"])
                if parsed:
                    source_type = "LIVE_WORK_RECORDS"
                    raw_rows.extend(parsed)

        logger.info(f"Discovery completed. Harvested {len(raw_rows)} raw items (Source type: {source_type}).")
        return raw_rows, target_url, status_code, source_type
