from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict

class DelaySeverityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"

class DelayTypeEnum(str, Enum):
    RECOMMENDATION_TO_SANCTION_DELAY = "RECOMMENDATION_TO_SANCTION_DELAY"
    SANCTION_TO_COMPLETION_DELAY = "SANCTION_TO_COMPLETION_DELAY"
    OPEN_WORK_AGING_STALLED = "OPEN_WORK_AGING_STALLED"

class DelayItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_id: str
    delay_score: float
    severity: str
    primary_delay_type: Optional[str] = None
    active_delay_types: Optional[List[str]] = None
    rec_to_sanc_days: Optional[int] = None
    rec_to_sanc_delay_days: Optional[int] = None
    rec_to_sanc_severity: Optional[str] = None
    sanc_to_comp_days: Optional[int] = None
    sanc_to_comp_delay_days: Optional[int] = None
    sanc_to_comp_severity: Optional[str] = None
    open_work_aging_days: Optional[int] = None
    open_work_overdue_days: Optional[int] = None
    open_work_aging_severity: Optional[str] = None
    explanation: Optional[str] = None

class DelayDetail(DelayItem):
    state: Optional[str] = None
    district: Optional[str] = None
    mp_name: Optional[str] = None
    work_status: Optional[str] = None
    sanction_date: Optional[str] = None
    recommended_date: Optional[str] = None
    completion_date: Optional[str] = None
