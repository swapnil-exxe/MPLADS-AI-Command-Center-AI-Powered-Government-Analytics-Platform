import logging
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.config import scraper_settings
from scraper.spider import LiveScraperPipeline

logger = logging.getLogger("scraper.scheduler")

class ScraperScheduler:
    """
    Background job scheduler for periodic live ingestion runs.
    Configurable via SCRAPER_INTERVAL_HOURS=6.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.pipeline = LiveScraperPipeline()

    def start(self):
        interval_hours = scraper_settings.SCRAPER_INTERVAL_HOURS
        logger.info(f"Starting Scraper Scheduler (Interval: {interval_hours} hours)...")

        self.scheduler.add_job(
            func=self.pipeline.run_pipeline,
            trigger="interval",
            hours=interval_hours,
            id="live_scraper_ingestion_job",
            name="Periodic Live eSAKSHI Ingestion Run",
            replace_existing=True
        )
        self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scraper Scheduler stopped.")
