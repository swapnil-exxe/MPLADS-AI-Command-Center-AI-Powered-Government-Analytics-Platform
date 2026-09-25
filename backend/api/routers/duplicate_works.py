from typing import Optional
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from sqlalchemy.orm import aliased
from database.models import DuplicateWorkResult, Work
from api.dependencies import get_db, PaginationParams
from api.auth import CurrentUser, OptionalUser, apply_duplicate_works_scope, verify_work_jurisdiction
from api.schemas.duplicate_work import DuplicatePairItem, WorkDuplicateLookupResponse, DuplicateSeverityEnum
from api.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/analytics/duplicate-works", tags=["Model 2 — Duplicate Work Detection"])

@router.get("", response_model=PaginatedResponse[DuplicatePairItem])
def list_duplicate_works(
    severity: Optional[str] = Query(None, description="Filter by severity tier (default HIGH)"),
    min_duplicate_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum duplicate score"),
    is_same_mp: Optional[bool] = Query(None, description="Filter where both works recommended by same MP"),
    is_same_constituency: Optional[bool] = Query(None, description="Filter where both works in same constituency"),
    state: Optional[str] = Query(None, description="Filter by State of either work in pair"),
    district: Optional[str] = Query(None, description="Filter by District of either work in pair"),
    pagination: PaginationParams = Depends(),
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Retrieves flagged duplicate candidate pairs with server-side RBAC scoping and state/district filters."""
    query = db.query(DuplicateWorkResult)

    if (state and state.strip()) or (district and district.strip()):
        w1 = aliased(Work)
        w2 = aliased(Work)
        query = query.join(w1, DuplicateWorkResult.work_id_1 == w1.work_id).join(
            w2, DuplicateWorkResult.work_id_2 == w2.work_id
        )
        if state and state.strip():
            query = query.filter(or_(func.upper(w1.state) == func.upper(state.strip()), func.upper(w2.state) == func.upper(state.strip())))
        if district and district.strip():
            query = query.filter(or_(func.upper(w1.district) == func.upper(district.strip()), func.upper(w2.district) == func.upper(district.strip())))

    # Server-side jurisdictional predicate injection for pairs
    query = apply_duplicate_works_scope(query, current_user)

    if severity and severity.strip():
        query = query.filter(DuplicateWorkResult.severity == severity.strip().upper())
    if min_duplicate_score is not None:
        query = query.filter(DuplicateWorkResult.duplicate_score >= min_duplicate_score)
    if is_same_mp is not None:
        query = query.filter(DuplicateWorkResult.is_same_mp == is_same_mp)
    if is_same_constituency is not None:
        query = query.filter(DuplicateWorkResult.is_same_constituency == is_same_constituency)

    total_records = query.count()
    total_pages = math.ceil(total_records / pagination.page_size) if total_records > 0 else 1
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1

    items = query.order_by(DuplicateWorkResult.duplicate_score.desc()).offset(pagination.offset).limit(pagination.page_size).all()
    pair_items = [DuplicatePairItem.model_validate(item) for item in items]

    return PaginatedResponse[DuplicatePairItem](
        items=pair_items,
        pagination=PaginationMeta(
            total_records=total_records,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.get("/pairs/{work_id:path}", response_model=WorkDuplicateLookupResponse)
def get_work_duplicate_pairs(
    work_id: str,
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Bidirectional lookup of all duplicate pairs involving the specified work_id with RBAC checks."""
    clean_id = work_id.strip()
    work = db.query(Work).filter(Work.work_id == clean_id).first()
    if not work:
        raise HTTPException(status_code=404, detail=f"Work with ID '{clean_id}' not found.")

    # Server-side 403 verification
    verify_work_jurisdiction(work, current_user)

    pairs = db.query(DuplicateWorkResult).filter(
        or_(DuplicateWorkResult.work_id_1 == clean_id, DuplicateWorkResult.work_id_2 == clean_id)
    ).order_by(DuplicateWorkResult.duplicate_score.desc()).all()

    formatted_pairs = [DuplicatePairItem.model_validate(p) for p in pairs]
    return WorkDuplicateLookupResponse(
        work_id=clean_id,
        total_flagged_pairs=len(formatted_pairs),
        pairs=formatted_pairs
    )
