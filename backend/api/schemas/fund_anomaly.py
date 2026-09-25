from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict

class FundSeverityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class FundAuditCategoryEnum(str, Enum):
    ACTIVE_EXPENDITURE = "ACTIVE_EXPENDITURE"
    NORMAL_AWAITING_DISBURSEMENT = "NORMAL_AWAITING_DISBURSEMENT"
    DORMANT_SANCTION = "DORMANT_SANCTION"
    STATUS_EXPENDITURE_MISMATCH = "STATUS_EXPENDITURE_MISMATCH"

class FundAnomalyItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_id: str
    fund_anomaly_score: float
    raw_score: Optional[float] = None
    severity: str
    audit_category: str
    total_disbursed_amount: Optional[float] = None
    utilization_ratio: Optional[float] = None
    transaction_count: Optional[int] = None
    payment_concentration_hhi: Optional[float] = None
    days_to_first_disbursement: Optional[float] = None
    anomaly_reasons: Optional[List[str]] = None
    explanation: Optional[str] = None

class FundAnomalyDetail(FundAnomalyItem):
    sanction_amount: Optional[float] = None
    work_status: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    mp_name: Optional[str] = None
