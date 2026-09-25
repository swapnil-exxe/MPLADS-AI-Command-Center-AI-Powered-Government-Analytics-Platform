from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RawSnapshotModel(BaseModel):
    snapshot_id: str
    snapshot_path: str
    source_url: str
    http_status: int
    content_hash: str
    records_extracted: int
    created_at: datetime = Field(default_factory=datetime.now)

class NormalizedWorkModel(BaseModel):
    work_id: str
    house: Optional[str] = None
    state: str
    district: str
    constituency: Optional[str] = None
    mp_name: Optional[str] = None
    ida: Optional[str] = None
    work_category: Optional[str] = None
    work_type: Optional[str] = None
    work_description: Optional[str] = None
    work_status: Optional[str] = None
    sanction_amount: Optional[float] = None
    sanction_date: Optional[str] = None
    recommended_date: Optional[str] = None
    completion_date: Optional[str] = None
    amount_disbursed: Optional[float] = None
    is_completed_flag: bool = False
    source_dataset: str = "OFFICIAL_LIVE_ESAKSHI"
    source_url: str = "https://mplads.mospi.gov.in/digigov/dashboard.html"
    source_hash: Optional[str] = None

class ValidationResultModel(BaseModel):
    is_valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    errors: List[str] = []
    warnings: List[str] = []

class ChangeLogEntryModel(BaseModel):
    work_id: str
    change_type: str  # NEW, UPDATED, UNCHANGED, DISAPPEARED_FROM_SOURCE, INVALID
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: List[str] = []
    detected_at: datetime = Field(default_factory=datetime.now)

class IngestionRunStatusModel(BaseModel):
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str  # RUNNING, COMPLETED, FAILED, NO_CHANGES
    records_seen: int = 0
    records_new: int = 0
    records_updated: int = 0
    records_unchanged: int = 0
    records_invalid: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
