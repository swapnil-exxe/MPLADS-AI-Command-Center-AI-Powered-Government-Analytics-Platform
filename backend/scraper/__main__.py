import sys
import argparse
import logging
from scraper.spider import LiveScraperPipeline
from scraper.scheduler import ScraperScheduler

logger = logging.getLogger("scraper.main")

def main():
    parser = argparse.ArgumentParser(description="Live Data Scraping & Ingestion Pipeline CLI")
    parser.add_argument("--once", action="store_true", help="Run a single live ingestion run and exit")
    parser.add_argument("--daemon", action="store_true", help="Start continuous scheduled background daemon")

    args = parser.parse_args()

    pipeline = LiveScraperPipeline()

    if args.once or len(sys.argv) == 1:
        logger.info("Executing single live ingestion run (--once)...")
        result = pipeline.run_pipeline()
        print("\n" + "="*50)
        print("LIVE INGESTION RUN COMPLETED")
        print("="*50)
        print(f"Run ID:            {result.run_id}")
        print(f"Status:            {result.status}")
        print(f"Records Seen:      {result.records_seen:,}")
        print(f"Records New:       {result.records_new:,}")
        print(f"Records Updated:   {result.records_updated:,}")
        print(f"Records Unchanged: {result.records_unchanged:,}")
        print(f"Records Invalid:   {result.records_invalid:,}")
        print(f"Duration:          {result.duration_seconds:.2f}s")
        if result.error_message:
            print(f"Error Message:     {result.error_message}")
        print("="*50 + "\n")
    elif args.daemon:
        logger.info("Starting Scraper Scheduler Daemon...")
        scheduler = ScraperScheduler()
        scheduler.start()
        try:
            while True:
                pass
        except (KeyboardInterrupt, SystemExit):
            scheduler.stop()

if __name__ == "__main__":
    main()
