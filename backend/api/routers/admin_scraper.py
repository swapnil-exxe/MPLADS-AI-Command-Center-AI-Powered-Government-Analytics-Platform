import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.dependencies import get_db
from api.auth.dependencies import CurrentUser, OptionalUser, require_roles
from database.models import User
from scraper.spider import LiveScraperPipeline
from scraper.config import scraper_settings

logger = logging.getLogger("api.admin_scraper")

router = APIRouter(prefix="/admin/scraper", tags=["Admin & Data Source Pipeline"])

@router.post("/run")
def trigger_manual_ingestion(
    background_tasks: BackgroundTasks,
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """
    Manually triggers an on-demand live eSAKSHI ingestion run in background task.
    Returns 200 OK immediately with job status.
    """
    user_email = current_user.email if current_user else "demo_public_user@mplads.gov.in"
    logger.info(f"Manual ingestion trigger requested by {user_email}")
    
    def _run_bg():
        try:
            pipeline = LiveScraperPipeline(db_session=db)
            pipeline.run_pipeline()
        except Exception as e:
            logger.error(f"Background ingestion run failed: {e}", exc_info=True)

    background_tasks.add_task(_run_bg)
    return {
        "status": "success",
        "message": "Live eSAKSHI ingestion run initiated successfully in background.",
        "target_url": scraper_settings.TARGET_URL,
        "initiated_at": datetime.now().isoformat()
    }

@router.get("/status")
def get_scraper_pipeline_status(
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """
    Returns current live pipeline status, last run metrics, and truthful source health.
    """
    # Fetch last ingestion run from DB
    sql_last_run = """
    SELECT run_id, start_time, end_time, status, records_seen, records_new,
           records_updated, records_unchanged, records_invalid, duration_seconds, error_message
    FROM ingestion_runs
    ORDER BY start_time DESC
    LIMIT 1;
    """
    last_run_row = db.execute(text(sql_last_run)).fetchone()

    last_run = None
    source_health = "READY"
    if last_run_row:
        last_run_status = last_run_row[3]
        last_run = {
            "run_id": last_run_row[0],
            "start_time": str(last_run_row[1]),
            "end_time": str(last_run_row[2]) if last_run_row[2] else None,
            "status": last_run_status,
            "records_seen": last_run_row[4] or 0,
            "records_new": last_run_row[5] or 0,
            "records_updated": last_run_row[6] or 0,
            "records_unchanged": last_run_row[7] or 0,
            "records_invalid": last_run_row[8] or 0,
            "duration_seconds": round(last_run_row[9], 2) if last_run_row[9] else 0.0,
            "error_message": last_run_row[10]
        }
        if last_run_status == "COMPLETED":
            source_health = "SUCCESS"
        elif last_run_status == "NO_CHANGES":
            source_health = "NO_CHANGES"
        elif last_run_status == "RUNNING":
            source_health = "RUNNING"
        elif last_run_status == "FAILED":
            source_health = "FAILED"

    # Fetch counts
    snapshot_count = db.execute(text("SELECT COUNT(*) FROM source_snapshots;")).scalar() or 0
    db_total_works = db.execute(text("SELECT COUNT(*) FROM works;")).scalar() or 0
    runs_count = db.execute(text("SELECT COUNT(*) FROM ingestion_runs;")).scalar() or 0

    return {
        "target_url": scraper_settings.TARGET_URL,
        "interval_hours": scraper_settings.SCRAPER_INTERVAL_HOURS,
        "source_type": "LIVE_DASHBOARD_SUMMARY",
        "status": "healthy" if source_health in ["SUCCESS", "NO_CHANGES", "READY", "RUNNING"] else "warning",
        "is_running": source_health == "RUNNING",
        "last_run": last_run,
        "total_snapshots_saved": snapshot_count,
        "total_works_in_db": db_total_works,
        "total_canonical_works": db_total_works,
        "total_ingestion_runs": runs_count,
        "source_health": source_health
    }
