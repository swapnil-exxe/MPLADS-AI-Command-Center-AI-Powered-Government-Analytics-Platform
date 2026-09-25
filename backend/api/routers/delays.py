from typing import Optional
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import DelayResult, Work
from api.dependencies import get_db, PaginationParams
from api.auth import CurrentUser, OptionalUser, apply_work_joined_scope, verify_work_jurisdiction
from api.schemas.delay import DelayItem, DelayDetail, DelaySeverityEnum, DelayTypeEnum
from api.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/analytics/delays", tags=["Model 4 — Statutory Delay & SLA Tracking"])

@router.get("", response_model=PaginatedResponse[DelayItem])
def list_delays(
    severity: Optional[str] = Query(None, description="Filter by delay severity tier"),
    primary_delay_type: Optional[str] = Query(None, description="Filter by statutory delay rule type"),
    min_days_overdue: Optional[int] = Query(None, ge=0, description="Minimum days overdue past statutory SLA"),
    state: Optional[str] = Query(None, description="Filter by State (via joined work)"),
    district: Optional[str] = Query(None, description="Filter by District (via joined work)"),
    pagination: PaginationParams = Depends(),
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Lists delayed or stalled works exceeding official statutory deadlines with server-side RBAC scoping."""
    query = db.query(DelayResult)

    already_joined = False
    if state and state.strip():
        query = query.join(Work, DelayResult.work_id == Work.work_id)
        already_joined = True
        query = query.filter(func.upper(Work.state) == func.upper(state.strip()))
    if district and district.strip():
        if not already_joined:
            query = query.join(Work, DelayResult.work_id == Work.work_id)
            already_joined = True
        query = query.filter(func.upper(Work.district) == func.upper(district.strip()))

    query, already_joined = apply_work_joined_scope(query, current_user, DelayResult, already_joined)

    if severity and severity.strip():
        query = query.filter(DelayResult.severity == severity.strip().upper())
    if primary_delay_type and primary_delay_type.strip():
        query = query.filter(DelayResult.primary_delay_type == primary_delay_type.strip().upper())
    if min_days_overdue is not None:
        query = query.filter(DelayResult.open_work_overdue_days >= min_days_overdue)

    total_records = query.count()
    total_pages = math.ceil(total_records / pagination.page_size) if total_records > 0 else 1
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1

    items = query.order_by(DelayResult.delay_score.desc()).offset(pagination.offset).limit(pagination.page_size).all()
    delay_items = [DelayItem.model_validate(item) for item in items]

    return PaginatedResponse[DelayItem](
        items=delay_items,
        pagination=PaginationMeta(
            total_records=total_records,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.get("/{work_id:path}", response_model=DelayDetail)
def get_delay_detail(
    work_id: str,
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Returns statutory SLA breakdown and exact days elapsed vs official guideline SLA with RBAC checks."""
    clean_id = work_id.strip()
    record = db.query(DelayResult, Work).join(Work, DelayResult.work_id == Work.work_id).filter(DelayResult.work_id == clean_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Delay record for work ID '{clean_id}' not found.")

    delay_res, work = record
    # Server-side 403 verification
    verify_work_jurisdiction(work, current_user)

    delay_dict = {c.name: getattr(delay_res, c.name) for c in delay_res.__table__.columns}

    return DelayDetail(
        **delay_dict,
        state=work.state,
        district=work.district,
        mp_name=work.mp_name,
        work_status=work.work_status,
        sanction_date=str(work.sanction_date) if work.sanction_date else None,
        recommended_date=str(work.recommended_date) if work.recommended_date else None,
        completion_date=str(work.completion_date) if work.completion_date else None
    )
