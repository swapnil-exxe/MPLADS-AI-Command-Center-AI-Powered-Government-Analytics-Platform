from typing import Optional
from pydantic import BaseModel

class DistrictSummaryItem(BaseModel):
    state: str
    district: str
    total_works: int
    total_sanctioned_amount: float
    total_disbursed_amount: float
    high_cost_anomalies: int
    high_duplicate_pairs: int
    high_fund_anomalies: int
    high_delays: int

class MPSummaryItem(BaseModel):
    mp_name: str
    house: str
    state: str
    constituency: Optional[str] = None
    total_works: int
    total_sanctioned_amount: float
    completed_works: int
    completion_rate: float
    high_cost_anomalies: int
    high_duplicate_pairs: int = 0
    high_fund_anomalies: int
    high_delays: int
