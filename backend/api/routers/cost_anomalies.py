from typing import Optional
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import CostAnomalyResult, Work
from api.dependencies import get_db, PaginationParams
from api.auth import CurrentUser, OptionalUser, apply_work_joined_scope, verify_work_jurisdiction
from api.schemas.cost_anomaly import CostAnomalyItem, CostAnomalyDetail, CostSeverityEnum
from api.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/analytics/cost-anomalies", tags=["Model 1 — Cost Anomaly Detection"])

@router.get("", response_model=PaginatedResponse[CostAnomalyItem])
def list_cost_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity tier"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum calibrated cost anomaly score"),
    state: Optional[str] = Query(None, description="Filter by State (via joined work)"),
    district: Optional[str] = Query(None, description="Filter by District (via joined work)"),
    peer_group_level: Optional[str] = Query(None, description="Filter by peer group granularity level"),
    pagination: PaginationParams = Depends(),
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Retrieves ranked cost anomaly detections with peer group context and server-side RBAC scoping."""
    query = db.query(CostAnomalyResult)

    already_joined = False
    if state and state.strip():
        query = query.join(Work, CostAnomalyResult.work_id == Work.work_id)
        already_joined = True
        query = query.filter(func.upper(Work.state) == state.strip().upper())
    if district and district.strip():
        if not already_joined:
            query = query.join(Work, CostAnomalyResult.work_id == Work.work_id)
            already_joined = True
        query = query.filter(func.upper(Work.district) == district.strip().upper())

    # Server-side jurisdictional predicate injection
    query, _ = apply_work_joined_scope(query, current_user, CostAnomalyResult, already_joined=already_joined)

    if severity and severity.strip():
        query = query.filter(CostAnomalyResult.severity == severity.strip().upper())
    if min_score is not None:
        query = query.filter(CostAnomalyResult.cost_anomaly_score >= min_score)
    if peer_group_level and peer_group_level.strip():
        query = query.filter(CostAnomalyResult.peer_group_level == peer_group_level.strip())

    total_records = query.count()
    items = query.order_by(CostAnomalyResult.cost_anomaly_score.desc()).offset(pagination.offset).limit(pagination.page_size).all()

    total_pages = math.ceil(total_records / pagination.page_size) if total_records > 0 else 1
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1

    formatted_items = [CostAnomalyItem.model_validate(item) for item in items]

    return PaginatedResponse[CostAnomalyItem](
        items=formatted_items,
        pagination=PaginationMeta(
            total_records=total_records,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.get("/{work_id:path}", response_model=CostAnomalyDetail)
def get_cost_anomaly_detail(
    work_id: str,
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Retrieves detailed cost anomaly diagnosis with joined work metadata and RBAC checks."""
    clean_id = work_id.strip()
    record = db.query(CostAnomalyResult, Work).join(Work, CostAnomalyResult.work_id == Work.work_id).filter(CostAnomalyResult.work_id == clean_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Cost anomaly record for work ID '{clean_id}' not found.")

    cost_res, work = record
    # Server-side 403 verification
    verify_work_jurisdiction(work, current_user)

    cost_dict = {c.name: getattr(cost_res, c.name) for c in cost_res.__table__.columns}

    return CostAnomalyDetail(
        **cost_dict,
        house=work.house,
        state=work.state,
        district=work.district,
        mp_name=work.mp_name,
        work_type=work.work_type,
        sanction_amount=work.sanction_amount
    )
