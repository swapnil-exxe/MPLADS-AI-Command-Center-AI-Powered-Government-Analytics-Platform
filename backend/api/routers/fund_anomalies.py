from typing import Optional
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import FundExpenditureResult, Work
from api.dependencies import get_db, PaginationParams
from api.auth import CurrentUser, OptionalUser, apply_work_joined_scope, verify_work_jurisdiction
from api.schemas.fund_anomaly import FundAnomalyItem, FundAnomalyDetail, FundSeverityEnum, FundAuditCategoryEnum
from api.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/analytics/fund-anomalies", tags=["Model 3 — Fund & Expenditure Anomaly"])

@router.get("", response_model=PaginatedResponse[FundAnomalyItem])
def list_fund_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity tier"),
    audit_category: Optional[str] = Query(None, description="Filter by financial audit category"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum calibrated fund anomaly score"),
    min_utilization: Optional[float] = Query(None, ge=0.0, description="Minimum utilization ratio"),
    max_utilization: Optional[float] = Query(None, ge=0.0, description="Maximum utilization ratio"),
    state: Optional[str] = Query(None, description="Filter by State (via joined work)"),
    district: Optional[str] = Query(None, description="Filter by District (via joined work)"),
    pagination: PaginationParams = Depends(),
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Lists fund and expenditure anomalies with lifecycle category filters and server-side RBAC scoping."""
    query = db.query(FundExpenditureResult)

    already_joined = False
    if state and state.strip():
        query = query.join(Work, FundExpenditureResult.work_id == Work.work_id)
        already_joined = True
        query = query.filter(func.upper(Work.state) == func.upper(state.strip()))
    if district and district.strip():
        if not already_joined:
            query = query.join(Work, FundExpenditureResult.work_id == Work.work_id)
            already_joined = True
        query = query.filter(func.upper(Work.district) == func.upper(district.strip()))

    query, already_joined = apply_work_joined_scope(query, current_user, FundExpenditureResult, already_joined)

    if severity and severity.strip():
        query = query.filter(FundExpenditureResult.severity == severity.strip().upper())
    if audit_category and audit_category.strip():
        query = query.filter(FundExpenditureResult.audit_category == audit_category.strip().upper())
    if min_score is not None:
        query = query.filter(FundExpenditureResult.fund_anomaly_score >= min_score)
    if min_utilization is not None:
        query = query.filter(FundExpenditureResult.utilization_ratio >= min_utilization)
    if max_utilization is not None:
        query = query.filter(FundExpenditureResult.utilization_ratio <= max_utilization)

    total_records = query.count()
    total_pages = math.ceil(total_records / pagination.page_size) if total_records > 0 else 1
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1

    items = query.order_by(FundExpenditureResult.fund_anomaly_score.desc()).offset(pagination.offset).limit(pagination.page_size).all()
    fund_items = [FundAnomalyItem.model_validate(item) for item in items]

    return PaginatedResponse[FundAnomalyItem](
        items=fund_items,
        pagination=PaginationMeta(
            total_records=total_records,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.get("/{work_id:path}", response_model=FundAnomalyDetail)
def get_fund_anomaly_detail(
    work_id: str,
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Returns granular fund utilization breakdown and transaction count for a single work with RBAC checks."""
    clean_id = work_id.strip()
    record = db.query(FundExpenditureResult, Work).join(Work, FundExpenditureResult.work_id == Work.work_id).filter(FundExpenditureResult.work_id == clean_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Fund anomaly record for work ID '{clean_id}' not found.")

    fund_res, work = record
    # Server-side 403 verification
    verify_work_jurisdiction(work, current_user)

    fund_dict = {c.name: getattr(fund_res, c.name) for c in fund_res.__table__.columns}

    return FundAnomalyDetail(
        **fund_dict,
        sanction_amount=work.sanction_amount,
        work_status=work.work_status,
        state=work.state,
        district=work.district,
        mp_name=work.mp_name
    )
