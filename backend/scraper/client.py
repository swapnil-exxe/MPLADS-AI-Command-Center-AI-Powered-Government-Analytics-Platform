import time
import subprocess
import json
import logging
from typing import Dict, Any, Optional
try:
    from scrapling import Fetcher
except ImportError:
    Fetcher = None

from scraper.config import scraper_settings

logger = logging.getLogger("scraper.client")
logging.basicConfig(level=logging.INFO)

class ResilientScraperClient:
    """
    Polite, resilient HTTP client combining Scrapling adaptive fetching
    with subprocess curl backoff for TLS/SSL handshake stability.
    """

    def __init__(self):
        try:
            self.fetcher = Fetcher() if Fetcher is not None else None
        except Exception:
            self.fetcher = None

    def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetches HTML page using Scrapling with fallback."""
        time.sleep(scraper_settings.RATE_LIMIT_DELAY_SECONDS)
        try:
            response = self.fetcher.get(url, timeout=scraper_settings.TIMEOUT_SECONDS)
            if response and hasattr(response, "text") and response.text:
                return {
                    "status_code": getattr(response, "status", 200),
                    "content": response.text,
                    "url": url,
                    "engine": "scrapling"
                }
        except Exception as e:
            logger.warning(f"Scrapling fetcher warning for {url}: {e}. Retrying via curl fallback.")

        # Fallback to curl subprocess if TLS handshaking restricts standard sockets
        cmd = [
            "curl", "-s", "-k",
            "-H", f"User-Agent: {scraper_settings.USER_AGENT}",
            "--max-time", str(scraper_settings.TIMEOUT_SECONDS),
            url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout:
            return {
                "status_code": 200,
                "content": res.stdout,
                "url": url,
                "engine": "curl_fallback"
            }
        
        return {
            "status_code": 500,
            "content": "",
            "url": url,
            "error": res.stderr or "Connection failed",
            "engine": "none"
        }

    def fetch_post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs POST request for public JSON APIs with resilient encoding handling."""
        time.sleep(scraper_settings.RATE_LIMIT_DELAY_SECONDS)
        cmd = [
            "curl", "-s", "-k",
            "-X", "POST",
            "-H", "Content-Type: application/json",
            "-H", f"User-Agent: {scraper_settings.USER_AGENT}",
            "-d", json.dumps(payload),
            "--max-time", str(scraper_settings.TIMEOUT_SECONDS),
            url
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and res.stdout:
            raw_text = res.stdout.decode("utf-8", errors="replace")
            try:
                data = json.loads(raw_text)
                return {
                    "status_code": 200,
                    "data": data,
                    "raw_text": raw_text,
                    "url": url
                }
            except json.JSONDecodeError:
                return {
                    "status_code": 200,
                    "data": None,
                    "raw_text": raw_text,
                    "url": url
                }

        err_text = res.stderr.decode("utf-8", errors="replace") if res.stderr else "Request failed"
        return {
            "status_code": 500,
            "data": None,
            "raw_text": "",
            "url": url,
            "error": err_text
        }
