import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class ScraperSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TARGET_URL: str = os.getenv("SCRAPER_TARGET_URL", "https://mplads.mospi.gov.in/digigov/dashboard.html")
    BASE_DOMAIN: str = os.getenv("SCRAPER_BASE_DOMAIN", "https://mplads.mospi.gov.in")
    SCRAPER_INTERVAL_HOURS: int = int(os.getenv("SCRAPER_INTERVAL_HOURS", "6"))
    RAW_SNAPSHOT_DIR: str = os.getenv("RAW_SNAPSHOT_DIR", "data/raw/live_source")
    CHANGE_LOG_DIR: str = os.getenv("CHANGE_LOG_DIR", "data/change_logs")
    TIMEOUT_SECONDS: int = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "15"))
    RATE_LIMIT_DELAY_SECONDS: float = float(os.getenv("SCRAPER_RATE_LIMIT_DELAY", "1.0"))
    MAX_RETRIES: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    USER_AGENT: str = os.getenv(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )

scraper_settings = ScraperSettings()
