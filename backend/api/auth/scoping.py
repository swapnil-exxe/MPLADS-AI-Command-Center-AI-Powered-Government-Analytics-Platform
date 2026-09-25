from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_, and_
from sqlalchemy.orm import aliased
from database.models import User, Work, DuplicateWorkResult


def apply_jurisdiction_scope(
    query,
    user: User,
    entity_class,
    state_col: str = "state",
    district_col: str = "district",
    mp_col: str = "mp_name"
):
    """
    Applies server-side jurisdictional boundary predicates directly to an entity query
    based on the user's role and assignments.
    """
    if not user or user.role == "MINISTRY":
        return query

    if user.role == "STATE_OFFICER" and user.assigned_state:
        state_attr = getattr(entity_class, state_col)
        return query.filter(state_attr == user.assigned_state)

    if user.role == "DISTRICT_OFFICER" and user.assigned_state and user.assigned_district:
        state_attr = getattr(entity_class, state_col)
        district_attr = getattr(entity_class, district_col)
        return query.filter(
            state_attr == user.assigned_state,
            district_attr == user.assigned_district
        )

    if user.role == "MP" and user.assigned_mp_name:
        mp_attr = getattr(entity_class, mp_col)
        return query.filter(mp_attr == user.assigned_mp_name)

    return query


def apply_work_joined_scope(
    query,
    user: User,
    result_model_class,
    already_joined: bool = False
) -> Tuple[any, bool]:
    """
    Applies jurisdiction scope to an anomaly result model by joining or using the Work table.
    Returns (updated_query, is_work_joined).
    """
    if not user or user.role == "MINISTRY":
        return query, already_joined

    if user.role == "STATE_OFFICER" and user.assigned_state:
        if not already_joined:
            query = query.join(Work, result_model_class.work_id == Work.work_id)
            already_joined = True
        query = query.filter(Work.state == user.assigned_state)
    elif user.role == "DISTRICT_OFFICER" and user.assigned_state and user.assigned_district:
        if not already_joined:
            query = query.join(Work, result_model_class.work_id == Work.work_id)
            already_joined = True
        query = query.filter(
            Work.state == user.assigned_state,
            Work.district == user.assigned_district
        )
    elif user.role == "MP" and user.assigned_mp_name:
        if not already_joined:
            query = query.join(Work, result_model_class.work_id == Work.work_id)
            already_joined = True
        query = query.filter(Work.mp_name == user.assigned_mp_name)

    return query, already_joined


def apply_duplicate_works_scope(query, user: User):
    """
    Applies jurisdiction scope to DuplicateWorkResult pairs.
    Pair is visible if either work falls within the user's assigned jurisdiction.
    """
    if not user or user.role == "MINISTRY":
        return query

    w1 = aliased(Work)
    w2 = aliased(Work)

    if user.role == "STATE_OFFICER" and user.assigned_state:
        query = query.join(w1, DuplicateWorkResult.work_id_1 == w1.work_id).join(
            w2, DuplicateWorkResult.work_id_2 == w2.work_id
        )
        return query.filter(
            or_(w1.state == user.assigned_state, w2.state == user.assigned_state)
        )

    if user.role == "DISTRICT_OFFICER" and user.assigned_state and user.assigned_district:
        query = query.join(w1, DuplicateWorkResult.work_id_1 == w1.work_id).join(
            w2, DuplicateWorkResult.work_id_2 == w2.work_id
        )
        return query.filter(
            or_(
                and_(w1.state == user.assigned_state, w1.district == user.assigned_district),
                and_(w2.state == user.assigned_state, w2.district == user.assigned_district)
            )
        )

    if user.role == "MP" and user.assigned_mp_name:
        query = query.join(w1, DuplicateWorkResult.work_id_1 == w1.work_id).join(
            w2, DuplicateWorkResult.work_id_2 == w2.work_id
        )
        return query.filter(
            or_(w1.mp_name == user.assigned_mp_name, w2.mp_name == user.assigned_mp_name)
        )

    return query


def verify_work_jurisdiction(work: Work, user: User) -> None:
    """
    Verifies that a specific Work falls within the user's assigned jurisdiction.
    Raises HTTP 403 Forbidden with a clear message if out of scope.
    """
    if not user or user.role == "MINISTRY":
        return

    if user.role == "STATE_OFFICER" and user.assigned_state:
        if work.state != user.assigned_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: Work '{work.work_id}' is in State '{work.state}', "
                    f"outside your assigned State '{user.assigned_state}'."
                )
            )

    elif user.role == "DISTRICT_OFFICER" and user.assigned_state and user.assigned_district:
        if work.state != user.assigned_state or work.district != user.assigned_district:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: Work '{work.work_id}' is in District '{work.district}, {work.state}', "
                    f"outside your assigned District '{user.assigned_district}, {user.assigned_state}'."
                )
            )

    elif user.role == "MP" and user.assigned_mp_name:
        if work.mp_name != user.assigned_mp_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: Work '{work.work_id}' was recommended by '{work.mp_name}', "
                    f"outside your assigned MP scrutiny scope '{user.assigned_mp_name}'."
                )
            )
