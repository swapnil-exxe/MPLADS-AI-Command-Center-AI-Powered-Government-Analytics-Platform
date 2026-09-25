"""
Production-grade Live Ingestion & Auto-Update Pipeline for MPLADS Governance Platform.
Powered by Scrapling for resilient public endpoint harvesting.
"""

from scraper.spider import LiveScraperPipeline
from scraper.scheduler import ScraperScheduler

__all__ = ["LiveScraperPipeline", "ScraperScheduler"]
