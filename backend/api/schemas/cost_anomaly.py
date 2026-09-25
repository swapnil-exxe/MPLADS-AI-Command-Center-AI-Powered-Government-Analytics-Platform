from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict

class CostSeverityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    DATA_QUALITY_EXCEPTION = "DATA_QUALITY_EXCEPTION"
    INSUFFICIENT_PEER_DATA = "INSUFFICIENT_PEER_DATA"

class CostAnomalyItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_id: str
    cost_anomaly_score: float
    raw_anomaly_score: Optional[float] = None
    severity: str
    peer_group_used: Optional[str] = None
    peer_group_level: Optional[str] = None
    peer_group_size: Optional[int] = None
    is_data_quality_exception: bool = False
    explanation: Optional[str] = None

class CostAnomalyDetail(CostAnomalyItem):
    house: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    mp_name: Optional[str] = None
    work_type: Optional[str] = None
    sanction_amount: Optional[float] = None
