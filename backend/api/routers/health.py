import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.dependencies import get_db
from api.schemas.common import HealthCheckResponse, FilterOptionsResponse
from api.config import settings

router = APIRouter(tags=["System & Metadata"])

@router.api_route("/health", methods=["GET", "HEAD"], response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    """Live health status and latency benchmark against Supabase PostgreSQL."""
    t0 = time.time()
    status_str = "healthy"
    db_name = "PostgreSQL on Supabase"
    count = 0
    try:
        count = db.execute(text("SELECT count(*) FROM works;")).scalar() or 0
    except Exception as e:
        status_str = "degraded"
        db_name = f"Database: {str(e)[:60]}"

    latency_ms = (time.time() - t0) * 1000.0

    return HealthCheckResponse(
        status=status_str,
        database=db_name,
        db_latency_ms=round(latency_ms, 2),
        total_works=count,
        version=settings.VERSION
    )

@router.get("/meta/filters", response_model=FilterOptionsResponse)
def get_filter_metadata(db: Session = Depends(get_db)):
    """Returns dynamic distinct filter values for frontend search dropdowns."""
    states = [r[0] for r in db.execute(text("SELECT DISTINCT state FROM works WHERE state IS NOT NULL ORDER BY state;")).fetchall()]
    districts = [r[0] for r in db.execute(text("SELECT DISTINCT district FROM works WHERE district IS NOT NULL ORDER BY district;")).fetchall()]
    houses = [r[0] for r in db.execute(text("SELECT DISTINCT house FROM works WHERE house IS NOT NULL ORDER BY house;")).fetchall()]
    categories = [r[0] for r in db.execute(text("SELECT DISTINCT work_category FROM works WHERE work_category IS NOT NULL ORDER BY work_category;")).fetchall()]
    statuses = [r[0] for r in db.execute(text("SELECT DISTINCT work_status FROM works WHERE work_status IS NOT NULL ORDER BY work_status;")).fetchall()]

    return FilterOptionsResponse(
        states=states,
        districts=districts,
        houses=houses,
        work_categories=categories,
        work_statuses=statuses,
        cost_severities=["HIGH", "MEDIUM", "LOW", "DATA_QUALITY_EXCEPTION", "INSUFFICIENT_PEER_DATA"],
        duplicate_severities=["HIGH", "REVIEW", "LOW"],
        fund_severities=["HIGH", "MEDIUM", "LOW"],
        fund_audit_categories=["ACTIVE_EXPENDITURE", "NORMAL_AWAITING_DISBURSEMENT", "DORMANT_SANCTION", "STATUS_EXPENDITURE_MISMATCH"],
        delay_severities=["HIGH", "MEDIUM", "LOW", "NONE"],
        delay_types=["RECOMMENDATION_TO_SANCTION_DELAY", "SANCTION_TO_COMPLETION_DELAY", "OPEN_WORK_AGING_STALLED"]
    )
