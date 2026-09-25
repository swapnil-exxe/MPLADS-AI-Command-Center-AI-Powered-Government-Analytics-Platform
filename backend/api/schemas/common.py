from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")

class PaginationMeta(BaseModel):
    total_records: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ProvenanceMeta(BaseModel):
    source: str = "supabase"
    records_analyzed: int
    generated_at: str
    model_version: str = "1.0.0"
    accuracy_status: str = "Accuracy unavailable — no validated ground-truth labels."

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationMeta
    provenance: Optional[ProvenanceMeta] = None

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    db_latency_ms: float
    total_works: int
    version: str

class FilterOptionsResponse(BaseModel):
    states: List[str]
    districts: List[str]
    houses: List[str]
    work_categories: List[str]
    work_statuses: List[str]
    cost_severities: List[str]
    duplicate_severities: List[str]
    fund_severities: List[str]
    fund_audit_categories: List[str]
    delay_severities: List[str]
    delay_types: List[str]
