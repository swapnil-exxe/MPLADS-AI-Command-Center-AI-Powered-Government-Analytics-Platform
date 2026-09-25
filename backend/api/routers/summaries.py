from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.dependencies import get_db
from api.auth import OptionalUser
from api.schemas.summaries import DistrictSummaryItem, MPSummaryItem

import time

router = APIRouter(prefix="/analytics", tags=["Aggregations & Governance Summaries"])

_DISTRICT_CACHE = None
_DISTRICT_CACHE_TIME = 0.0
CACHE_TTL_SECONDS = 60.0


def _build_district_summary_data(db: Session, where_clause: str, params: dict) -> List[DistrictSummaryItem]:
    # 1. Base Works aggregation by district (Ultra-fast index-backed scan)
    sql_base = f"""
    SELECT
        w.state,
        w.district,
        count(w.work_id) AS total_works,
        COALESCE(sum(w.sanction_amount), 0) AS total_sanctioned_amount,
        COALESCE(sum(w.amount_disbursed), 0) AS total_disbursed_amount
    FROM works w
    {where_clause}
    GROUP BY w.state, w.district
    ORDER BY total_sanctioned_amount DESC
    LIMIT :limit;
    """
    rows = db.execute(text(sql_base), params).fetchall()
    if not rows:
        return []

    # 2. High Cost Anomalies lookup cache by district
    cost_cache = {}
    try:
        sql_cost = """
        SELECT UPPER(w.state), UPPER(w.district), count(DISTINCT c.work_id)
        FROM cost_anomaly_results c
        JOIN works w ON c.work_id = w.work_id
        WHERE c.severity = 'HIGH'
        GROUP BY UPPER(w.state), UPPER(w.district);
        """
        cost_cache = {(r[0], r[1]): r[2] for r in db.execute(text(sql_cost)).fetchall()}
    except Exception as e:
        print(f"[SUMMARY WARN] cost_cache query failed: {e}")

    # 3. High Delay Violations lookup cache by district
    delay_cache = {}
    try:
        sql_delay = """
        SELECT UPPER(w.state), UPPER(w.district), count(DISTINCT d.work_id)
        FROM delay_results d
        JOIN works w ON d.work_id = w.work_id
        WHERE d.severity = 'HIGH'
        GROUP BY UPPER(w.state), UPPER(w.district);
        """
        delay_cache = {(r[0], r[1]): r[2] for r in db.execute(text(sql_delay)).fetchall()}
    except Exception as e:
        print(f"[SUMMARY WARN] delay_cache query failed: {e}")

    # 4. High Fund Expenditure Anomalies lookup cache by district
    fund_cache = {}
    try:
        sql_fund = """
        SELECT UPPER(w.state), UPPER(w.district), count(DISTINCT f.work_id)
        FROM fund_expenditure_results f
        JOIN works w ON f.work_id = w.work_id
        WHERE f.severity = 'HIGH'
        GROUP BY UPPER(w.state), UPPER(w.district);
        """
        fund_cache = {(r[0], r[1]): r[2] for r in db.execute(text(sql_fund)).fetchall()}
    except Exception as e:
        print(f"[SUMMARY WARN] fund_cache query failed: {e}")

    # 5. High Duplicate Pairs lookup cache by district
    dup_cache = {}
    try:
        sql_dup = """
        SELECT state, district, count(DISTINCT dup_id) as dup_count FROM (
            SELECT UPPER(w.state) as state, UPPER(w.district) as district, dup.id as dup_id
            FROM duplicate_work_results dup
            JOIN works w ON dup.work_id_1 = w.work_id
            WHERE dup.severity = 'HIGH'
            UNION ALL
            SELECT UPPER(w.state) as state, UPPER(w.district) as district, dup.id as dup_id
            FROM duplicate_work_results dup
            JOIN works w ON dup.work_id_2 = w.work_id
            WHERE dup.severity = 'HIGH'
        ) sub
        GROUP BY state, district;
        """
        dup_cache = {(r[0], r[1]): r[2] for r in db.execute(text(sql_dup)).fetchall()}
    except Exception as e:
        print(f"[SUMMARY WARN] dup_cache query failed: {e}")

    results = []
    for r in rows:
        st, dist = r[0], r[1]
        key = (str(st).upper(), str(dist).upper())
        results.append(DistrictSummaryItem(
            state=st,
            district=dist,
            total_works=r[2],
            total_sanctioned_amount=float(r[3]),
            total_disbursed_amount=float(r[4]),
            high_cost_anomalies=cost_cache.get(key, 0),
            high_delays=delay_cache.get(key, 0),
            high_fund_anomalies=fund_cache.get(key, 0),
            high_duplicate_pairs=dup_cache.get(key, 0)
        ))
    return results


@router.get("/district-summary", response_model=List[DistrictSummaryItem])
def get_district_summary(
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: Optional[int] = Query(None, ge=1, le=5000, description="Max districts to return"),
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Aggregates work counts, budgets, and independent high-severity flags by district with RBAC scoping and fast TTL caching."""
    global _DISTRICT_CACHE, _DISTRICT_CACHE_TIME

    actual_limit = limit if limit is not None else 5000
    where_conditions = []
    params = {"limit": actual_limit}

    if current_user:
        if current_user.role == "STATE_OFFICER":
            where_conditions.append("UPPER(w.state) = UPPER(:user_state)")
            params["user_state"] = current_user.assigned_state
        elif current_user.role == "DISTRICT_OFFICER":
            where_conditions.append("UPPER(w.state) = UPPER(:user_state) AND UPPER(w.district) = UPPER(:user_district)")
            params["user_state"] = current_user.assigned_state
            params["user_district"] = current_user.assigned_district
        elif current_user.role == "MP":
            where_conditions.append("w.mp_name = :user_mp_name")
            params["user_mp_name"] = current_user.assigned_mp_name

    if state:
        where_conditions.append("UPPER(w.state) = UPPER(:filter_state)")
        params["filter_state"] = state

    # Unfiltered global request: Use fast 60s TTL memory cache
    is_global_request = not where_conditions and not state and not current_user
    now = time.time()

    if is_global_request and _DISTRICT_CACHE is not None and (now - _DISTRICT_CACHE_TIME) < CACHE_TTL_SECONDS:
        return _DISTRICT_CACHE[:actual_limit]

    where_clause = ("WHERE " + " AND ".join(where_conditions)) if where_conditions else ""

    try:
        data = _build_district_summary_data(db, where_clause, params)
        if is_global_request and data:
            _DISTRICT_CACHE = data
            _DISTRICT_CACHE_TIME = now
        return data
    except Exception as e:
        print(f"[SUMMARY ERROR] district summary query failed: {e}")
        return _DISTRICT_CACHE[:actual_limit] if _DISTRICT_CACHE else []

@router.get("/mp-summary", response_model=List[MPSummaryItem])
def get_mp_summary(
    mp_name: Optional[str] = Query(None, description="Search keyword in MP name"),
    limit: Optional[int] = Query(None, ge=1, le=5000, description="Max MPs to return"),
    current_user: OptionalUser = None,
    db: Session = Depends(get_db)
):
    """Aggregates work counts, completion rate, and independent risk counts by MP with RBAC scoping."""
    actual_limit = limit if limit is not None else 5000
    where_conditions = ["w.mp_name IS NOT NULL"]
    params = {"limit": actual_limit}

    if current_user:
        if current_user.role == "STATE_OFFICER":
            where_conditions.append("w.state = :user_state")
            params["user_state"] = current_user.assigned_state
        elif current_user.role == "DISTRICT_OFFICER":
            where_conditions.append("w.state = :user_state AND w.district = :user_district")
            params["user_state"] = current_user.assigned_state
            params["user_district"] = current_user.assigned_district
        elif current_user.role == "MP":
            where_conditions.append("w.mp_name = :user_mp_name")
            params["user_mp_name"] = current_user.assigned_mp_name

    if mp_name:
        where_conditions.append("w.mp_name ILIKE :filter_mp_name")
        params["filter_mp_name"] = f"%{mp_name}%"

    where_clause = "WHERE " + " AND ".join(where_conditions)
    sql = f"""
    SELECT
        w.mp_name,
        COALESCE(max(w.house), 'Lok Sabha') AS house,
        COALESCE(max(w.state), 'Unknown') AS state,
        COALESCE(max(w.constituency), 'Unknown') AS constituency,
        count(DISTINCT w.work_id) AS total_works,
        COALESCE(sum(w.sanction_amount), 0) AS total_sanctioned_amount,
        count(DISTINCT CASE WHEN w.is_completed_flag THEN w.work_id END) AS completed_works,
        count(DISTINCT c.work_id) AS high_cost_anomalies,
        count(DISTINCT f.work_id) AS high_fund_anomalies,
        count(DISTINCT d.work_id) AS high_delays
    FROM works w
    LEFT JOIN cost_anomaly_results c ON w.work_id = c.work_id AND c.severity = 'HIGH'
    LEFT JOIN fund_expenditure_results f ON w.work_id = f.work_id AND f.severity = 'HIGH'
    LEFT JOIN delay_results d ON w.work_id = d.work_id AND d.severity = 'HIGH'
    {where_clause}
    GROUP BY w.mp_name
    ORDER BY total_works DESC
    LIMIT :limit;
    """

    rows = db.execute(text(sql), params).fetchall()

    # Exact DB-level aggregation of high duplicate pairs by MP
    dup_cache = {}
    try:
        sql_dup = """
        SELECT mp_name, count(DISTINCT dup_id) as dup_count FROM (
            SELECT w.mp_name as mp_name, dup.id as dup_id
            FROM duplicate_work_results dup
            JOIN works w ON dup.work_id_1 = w.work_id
            WHERE dup.severity = 'HIGH' AND w.mp_name IS NOT NULL
            UNION ALL
            SELECT w.mp_name as mp_name, dup.id as dup_id
            FROM duplicate_work_results dup
            JOIN works w ON dup.work_id_2 = w.work_id
            WHERE dup.severity = 'HIGH' AND w.mp_name IS NOT NULL
        ) sub
        GROUP BY mp_name;
        """
        dup_rows = db.execute(text(sql_dup)).fetchall()
        dup_cache = {r[0]: r[1] for r in dup_rows}
    except Exception as e:
        print(f"[SUMMARY WARN] mp dup_cache query failed: {e}")
        dup_cache = {}

    results = []
    for r in rows:
        tot = r[4]
        comp = r[6]
        mp = r[0]
        rate = round((comp / tot) * 100.0, 1) if tot > 0 else 0.0
        dup_count = dup_cache.get(mp, 0)
        results.append(MPSummaryItem(
            mp_name=mp,
            house=r[1],
            state=r[2],
            constituency=r[3],
            total_works=tot,
            total_sanctioned_amount=float(r[5]),
            completed_works=comp,
            completion_rate=rate,
            high_cost_anomalies=r[7],
            high_duplicate_pairs=dup_count,
            high_fund_anomalies=r[8],
            high_delays=r[9]
        ))
    return results
