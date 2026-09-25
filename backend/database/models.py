from sqlalchemy import (
    Column,
    String,
    Numeric,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
    BigInteger,
    ForeignKey,
    Index,
    UniqueConstraint,
    JSON,
    func
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Work(Base):
    """Canonical Work table storing master metadata across all active works."""
    __tablename__ = "works"

    work_id = Column(String(255), primary_key=True)
    house = Column(String(32), nullable=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    ida = Column(String(100), nullable=True)
    mp_name = Column(String(150), nullable=True, index=True)
    constituency = Column(String(150), nullable=True)
    constituency_or_term = Column(String(150), nullable=True)
    work_category = Column(String(100), nullable=True)
    work_type = Column(String(255), nullable=True, index=True)
    work_description = Column(Text, nullable=True)
    work_status = Column(String(100), nullable=True, index=True)
    sanction_amount = Column(Numeric(15, 2), nullable=True)
    sanction_date = Column(Date, nullable=True, index=True)
    recommended_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    amount_disbursed = Column(Numeric(15, 2), nullable=True)
    is_completed_flag = Column(Boolean, default=False)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One-to-one relationships to module outputs
    cost_result = relationship("CostAnomalyResult", back_populates="work", uselist=False, cascade="all, delete-orphan")
    fund_result = relationship("FundExpenditureResult", back_populates="work", uselist=False, cascade="all, delete-orphan")
    delay_result = relationship("DelayResult", back_populates="work", uselist=False, cascade="all, delete-orphan")
    expenditures = relationship("WorkExpenditure", back_populates="work", cascade="all, delete-orphan")


class CostAnomalyResult(Base):
    """Model 1: Anomalous Cost Estimate Detector results."""
    __tablename__ = "cost_anomaly_results"

    work_id = Column(String(255), ForeignKey("works.work_id", ondelete="CASCADE"), primary_key=True)
    cost_anomaly_score = Column(Float, nullable=False, index=True)
    raw_anomaly_score = Column(Float, nullable=True)
    severity = Column(String(32), nullable=False, index=True)
    peer_group_used = Column(String(255), nullable=True)
    peer_group_level = Column(String(64), nullable=True)
    peer_group_size = Column(Integer, nullable=True)
    is_data_quality_exception = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)

    work = relationship("Work", back_populates="cost_result")


class DuplicateWorkResult(Base):
    """Model 2: Pair-level duplicate candidate detection results."""
    __tablename__ = "duplicate_work_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    work_id_1 = Column(String(255), ForeignKey("works.work_id", ondelete="CASCADE"), nullable=False, index=True)
    work_id_2 = Column(String(255), ForeignKey("works.work_id", ondelete="CASCADE"), nullable=False, index=True)
    duplicate_score = Column(Float, nullable=False, index=True)
    severity = Column(String(32), nullable=False, index=True)
    confidence = Column(Float, nullable=True)
    semantic_similarity = Column(Float, nullable=True)
    structural_score = Column(Float, nullable=True)
    amount_similarity = Column(Float, nullable=True)
    date_proximity = Column(Float, nullable=True)
    days_diff = Column(Integer, nullable=True)
    is_same_mp = Column(Boolean, nullable=True)
    is_same_constituency = Column(Boolean, nullable=True)
    explanation = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("work_id_1", "work_id_2", name="uq_duplicate_pair"),
        Index("idx_dup_pair_lookup", "work_id_1", "work_id_2"),
    )


class FundExpenditureResult(Base):
    """Model 3: Fund & Expenditure Anomaly Detector results."""
    __tablename__ = "fund_expenditure_results"

    work_id = Column(String(255), ForeignKey("works.work_id", ondelete="CASCADE"), primary_key=True)
    fund_anomaly_score = Column(Float, nullable=False, index=True)
    raw_score = Column(Float, nullable=True)
    severity = Column(String(32), nullable=False, index=True)
    audit_category = Column(String(64), nullable=True, index=True)
    total_disbursed_amount = Column(Numeric(15, 2), nullable=True)
    utilization_ratio = Column(Float, nullable=True)
    transaction_count = Column(Integer, nullable=True)
    payment_concentration_hhi = Column(Float, nullable=True)
    days_to_first_disbursement = Column(Float, nullable=True)
    anomaly_reasons = Column(JSON().with_variant(ARRAY(String), "postgresql"), nullable=True)
    explanation = Column(Text, nullable=True)

    work = relationship("Work", back_populates="fund_result")


class DelayResult(Base):
    """Phase 5: Delay & SLA Rule Engine results."""
    __tablename__ = "delay_results"

    work_id = Column(String(255), ForeignKey("works.work_id", ondelete="CASCADE"), primary_key=True)
    delay_score = Column(Float, nullable=False, index=True)
    severity = Column(String(32), nullable=False, index=True)
    primary_delay_type = Column(String(64), nullable=True, index=True)
    active_delay_types = Column(JSON().with_variant(ARRAY(String), "postgresql"), nullable=True)
    rec_to_sanc_days = Column(Integer, nullable=True)
    rec_to_sanc_delay_days = Column(Integer, nullable=True)
    rec_to_sanc_severity = Column(String(32), nullable=True)
    sanc_to_comp_days = Column(Integer, nullable=True)
    sanc_to_comp_delay_days = Column(Integer, nullable=True)
    sanc_to_comp_severity = Column(String(32), nullable=True)
    open_work_aging_days = Column(Integer, nullable=True)
    open_work_overdue_days = Column(Integer, nullable=True)
    open_work_aging_severity = Column(String(32), nullable=True)
    explanation = Column(Text, nullable=True)

    work = relationship("Work", back_populates="delay_result")


class WorkExpenditure(Base):
    """Work-level transaction vouchers linking expenditures to canonical works."""
    __tablename__ = "work_expenditures"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    work_id = Column(String(255), ForeignKey("works.work_id", ondelete="CASCADE"), nullable=False, index=True)
    expenditure_date = Column(Date, nullable=True, index=True)
    vendor_name = Column(String(255), nullable=True)
    fund_disbursed_amount = Column(Numeric(15, 2), nullable=True)
    payment_status = Column(String(64), nullable=True)

    work = relationship("Work", back_populates="expenditures")


class User(Base):
    """User accounts and role-based jurisdictional assignments (Phase 6.3)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(32), nullable=False, index=True)  # MINISTRY, STATE_OFFICER, DISTRICT_OFFICER, MP
    assigned_state = Column(String(100), nullable=True)
    assigned_district = Column(String(100), nullable=True)
    assigned_mp_name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SourceSnapshot(Base):
    """Raw scraper HTML/JSON source snapshot metadata."""
    __tablename__ = "source_snapshots"

    id = Column(String(64), primary_key=True)
    snapshot_path = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    http_status = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=False)
    records_extracted = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IngestionRun(Base):
    """Scraper ingestion execution log and summary statistics."""
    __tablename__ = "ingestion_runs"

    run_id = Column(String(64), primary_key=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), nullable=False)
    records_seen = Column(Integer, default=0)
    records_new = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_unchanged = Column(Integer, default=0)
    records_invalid = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)


class IngestionChange(Base):
    """Audit log of individual field-level changes detected by scraper."""
    __tablename__ = "ingestion_changes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("ingestion_runs.run_id", ondelete="CASCADE"), nullable=False)
    work_id = Column(String(64), nullable=False)
    change_type = Column(String(32), nullable=False)
    old_value_json = Column(Text, nullable=True)
    new_value_json = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())


class ScraperError(Base):
    """Error logs during scraper parsing and ingestion."""
    __tablename__ = "scraper_errors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("ingestion_runs.run_id", ondelete="CASCADE"), nullable=True)
    stage = Column(String(64), nullable=False)
    error_type = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


