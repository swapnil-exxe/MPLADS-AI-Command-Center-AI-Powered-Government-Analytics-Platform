from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from api.schemas.cost_anomaly import CostAnomalyItem
from api.schemas.fund_anomaly import FundAnomalyItem
from api.schemas.delay import DelayItem
from api.schemas.duplicate_work import DuplicatePairItem

class WorkExpenditureItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expenditure_date: Optional[str] = None
    vendor_name: Optional[str] = None
    fund_disbursed_amount: Optional[float] = None
    payment_status: Optional[str] = None

class WorkListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_id: str
    house: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    ida: Optional[str] = None
    mp_name: Optional[str] = None
    constituency: Optional[str] = None
    work_category: Optional[str] = None
    work_type: Optional[str] = None
    work_description: Optional[str] = None
    work_status: Optional[str] = None
    sanction_amount: Optional[float] = None
    sanction_date: Optional[str] = None
    recommended_date: Optional[str] = None
    completion_date: Optional[str] = None
    amount_disbursed: Optional[float] = None
    is_completed_flag: Optional[bool] = None

class IndependentModelProfiles(BaseModel):
    """Zero composite aggregation: strictly independent analytical evaluations."""
    cost_anomaly: Optional[CostAnomalyItem] = None
    duplicate_pairs: List[DuplicatePairItem] = []
    fund_anomaly: Optional[FundAnomalyItem] = None
    delay: Optional[DelayItem] = None

class WorkDetail(WorkListItem):
    expenditures: List[WorkExpenditureItem] = []
    independent_risk_profiles: IndependentModelProfiles
