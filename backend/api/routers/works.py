from typing import Optional
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from database.models import Work, WorkExpenditure, CostAnomalyResult, FundExpenditureResult, DelayResult, DuplicateWorkResult
from api.dependencies import get_db, PaginationParams
from api.auth import CurrentUser, OptionalUser, apply_jurisdiction_scope, verify_work_jurisdiction
from api.schemas.works import WorkListItem, WorkDetail, WorkExpenditureItem, IndependentModelProfiles
from api.schemas.common import PaginatedResponse, PaginationMeta
from api.schemas.cost_anomaly import CostAnomalyItem
from api.schemas.fund_anomaly import FundAnomalyItem
from api.schemas.delay import DelayItem
from api.schemas.duplicate_work import DuplicatePairItem

router = APIRouter(prefix="/works", tags=["Works Master Registry"])

@router.get("", response_model=PaginatedResponse[WorkListItem])
def list_works(
    state: Optional[str] = Query(None, description="Filter by State"),
    district: Optional[str] = Query(None, description="Filter by District"),
    mp_name: Optional[str] = Query(None, description="Filter by MP Name"),
    house: Optional[str] = Query(None, description="Filter by House (Lok Sabha / Rajya Sabha)"),
    work_category: Optional[str] = Query(None, description="Filter by Category"),
    work_status: Optional[str] = Query(None, description="Filter by Status"),
    min_sanction_amount: Optional[float] = Query(None, ge=0),
    max_sanction_amount: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None, description="Search keyword in work description"),
    pagination: PaginationParams = Depends(),
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Lists works with multi-attribute filtering, pagination, and server-side RBAC scoping."""
    query = db.query(Work)

    # Server-side jurisdictional predicate injection
    query = apply_jurisdiction_scope(query, current_user, Work)


    if state:
        query = query.filter(Work.state == state)
    if district:
        query = query.filter(Work.district == district)
    if mp_name:
        query = query.filter(Work.mp_name.ilike(f"%{mp_name}%"))
    if house:
        query = query.filter(Work.house == house)
    if work_category:
        query = query.filter(Work.work_category == work_category)
    if work_status:
        query = query.filter(Work.work_status == work_status)
    if min_sanction_amount is not None:
        query = query.filter(Work.sanction_amount >= min_sanction_amount)
    if max_sanction_amount is not None:
        query = query.filter(Work.sanction_amount <= max_sanction_amount)
    if search:
        query = query.filter(Work.work_description.ilike(f"%{search}%"))

    total_records = query.count()
    items = query.order_by(Work.sanction_date.desc().nullslast()).offset(pagination.offset).limit(pagination.page_size).all()

    total_pages = math.ceil(total_records / pagination.page_size) if total_records > 0 else 1
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1

    formatted_items = []
    for w in items:
        item_dict = {c.name: getattr(w, c.name) for c in w.__table__.columns}
        for dcol in ["sanction_date", "recommended_date", "completion_date"]:
            if item_dict.get(dcol):
                item_dict[dcol] = str(item_dict[dcol])
        formatted_items.append(WorkListItem(**item_dict))

    return PaginatedResponse[WorkListItem](
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

@router.get("/{work_id:path}", response_model=WorkDetail)
def get_work_detail(
    work_id: str,
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Returns deep-dive dossier for a single work with all 4 independent model assessments and RBAC checks."""
    clean_id = work_id.strip()
    work = db.query(Work).filter(Work.work_id == clean_id).first()
    if not work:
        raise HTTPException(status_code=404, detail=f"Work with ID '{clean_id}' not found.")

    # Server-side 403 verification for existing out-of-jurisdiction work
    verify_work_jurisdiction(work, current_user)

    expenditures = db.query(WorkExpenditure).filter(WorkExpenditure.work_id == work_id.strip()).order_by(WorkExpenditure.expenditure_date.asc()).all()
    exp_items = []
    for e in expenditures:
        exp_items.append(WorkExpenditureItem(
            id=e.id,
            expenditure_date=str(e.expenditure_date) if e.expenditure_date else None,
            vendor_name=e.vendor_name,
            fund_disbursed_amount=e.fund_disbursed_amount,
            payment_status=e.payment_status
        ))

    # Model 1: Cost Anomaly
    cost_res = db.query(CostAnomalyResult).filter(CostAnomalyResult.work_id == work_id.strip()).first()
    cost_item = CostAnomalyItem.model_validate(cost_res) if cost_res else None

    # Model 2: Duplicate Pairs (Bidirectional search)
    dup_res = db.query(DuplicateWorkResult).filter(
        or_(DuplicateWorkResult.work_id_1 == work_id.strip(), DuplicateWorkResult.work_id_2 == work_id.strip())
    ).order_by(DuplicateWorkResult.duplicate_score.desc()).all()
    dup_items = [DuplicatePairItem.model_validate(d) for d in dup_res]

    # Model 3: Fund Anomaly
    fund_res = db.query(FundExpenditureResult).filter(FundExpenditureResult.work_id == work_id.strip()).first()
    fund_item = FundAnomalyItem.model_validate(fund_res) if fund_res else None

    # Phase 5: Delay
    delay_res = db.query(DelayResult).filter(DelayResult.work_id == work_id.strip()).first()
    delay_item = DelayItem.model_validate(delay_res) if delay_res else None

    work_dict = {c.name: getattr(work, c.name) for c in work.__table__.columns}
    for dcol in ["sanction_date", "recommended_date", "completion_date"]:
        if work_dict.get(dcol):
            work_dict[dcol] = str(work_dict[dcol])

    # Defensive runtime reconciliation: if amount_disbursed is None/0 but vouchers exist, coalesce with voucher sum
    if (work_dict.get("amount_disbursed") is None or float(work_dict.get("amount_disbursed") or 0.0) == 0.0) and exp_items:
        voucher_total = sum(float(e.fund_disbursed_amount or 0.0) for e in exp_items)
        if voucher_total > 0:
            work_dict["amount_disbursed"] = voucher_total

    return WorkDetail(
        **work_dict,
        expenditures=exp_items,
        independent_risk_profiles=IndependentModelProfiles(
            cost_anomaly=cost_item,
            duplicate_pairs=dup_items,
            fund_anomaly=fund_item,
            delay=delay_item
        )
    )
