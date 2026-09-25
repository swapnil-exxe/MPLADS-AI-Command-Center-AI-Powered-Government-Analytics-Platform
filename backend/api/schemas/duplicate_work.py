from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict

class DuplicateSeverityEnum(str, Enum):
    HIGH = "HIGH"
    REVIEW = "REVIEW"
    LOW = "LOW"

class DuplicatePairItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    work_id_1: str
    work_id_2: str
    duplicate_score: float
    severity: str
    confidence: Optional[float] = None
    semantic_similarity: Optional[float] = None
    structural_score: Optional[float] = None
    amount_similarity: Optional[float] = None
    date_proximity: Optional[float] = None
    days_diff: Optional[int] = None
    is_same_mp: Optional[bool] = None
    is_same_constituency: Optional[bool] = None
    explanation: Optional[str] = None

class WorkDuplicateLookupResponse(BaseModel):
    work_id: str
    total_flagged_pairs: int
    pairs: List[DuplicatePairItem]
