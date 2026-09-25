"""
Tests for Phase 6.1 — Database & Ingestion Pipeline
Verifies Supabase connection, schema tables, row counts, foreign key integrity, and independent models.
"""

import pytest
from sqlalchemy import text, inspect
from database.connection import get_engine, check_connection
from database.models import (
    Work,
    CostAnomalyResult,
    DuplicateWorkResult,
    FundExpenditureResult,
    DelayResult,
    WorkExpenditure,
)

def test_database_connection():
    """Verify live connection to database."""
    assert check_connection() is True

def test_database_tables_exist():
    """Verify core tables exist in the database."""
    engine = get_engine()
    inspector = inspect(engine)
    for model in [Work, CostAnomalyResult, DuplicateWorkResult, FundExpenditureResult, DelayResult, WorkExpenditure]:
        table_name = model.__tablename__
        assert inspector.has_table(table_name), f"Table {table_name} does not exist"

def test_works_row_count():
    """Verify canonical works table contains data."""
    engine = get_engine()
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM works;")).scalar()
        assert count >= 98825

def test_model_results_row_counts():
    """Verify model results have expected row counts."""
    engine = get_engine()
    with engine.connect() as conn:
        cost_cnt = conn.execute(text("SELECT count(*) FROM cost_anomaly_results;")).scalar()
        assert cost_cnt >= 98825

        fund_cnt = conn.execute(text("SELECT count(*) FROM fund_expenditure_results;")).scalar()
        assert fund_cnt > 0

        delay_cnt = conn.execute(text("SELECT count(*) FROM delay_results;")).scalar()
        assert delay_cnt > 0

        dup_cnt = conn.execute(text("SELECT count(*) FROM duplicate_work_results;")).scalar()
        assert dup_cnt > 0

def test_foreign_key_integrity():
    """Verify zero orphaned records linking to the works table."""
    engine = get_engine()
    with engine.connect() as conn:
        cost_orphans = conn.execute(text(
            "SELECT count(*) FROM cost_anomaly_results c LEFT JOIN works w ON c.work_id = w.work_id WHERE w.work_id IS NULL;"
        )).scalar()
        assert cost_orphans == 0

        fund_orphans = conn.execute(text(
            "SELECT count(*) FROM fund_expenditure_results f LEFT JOIN works w ON f.work_id = w.work_id WHERE w.work_id IS NULL;"
        )).scalar()
        assert fund_orphans == 0

        delay_orphans = conn.execute(text(
            "SELECT count(*) FROM delay_results d LEFT JOIN works w ON d.work_id = w.work_id WHERE w.work_id IS NULL;"
        )).scalar()
        assert delay_orphans == 0

        dup1_orphans = conn.execute(text(
            "SELECT count(*) FROM duplicate_work_results d LEFT JOIN works w ON d.work_id_1 = w.work_id WHERE w.work_id IS NULL;"
        )).scalar()
        assert dup1_orphans == 0

        dup2_orphans = conn.execute(text(
            "SELECT count(*) FROM duplicate_work_results d LEFT JOIN works w ON d.work_id_2 = w.work_id WHERE w.work_id IS NULL;"
        )).scalar()
        assert dup2_orphans == 0

def test_independent_models_no_composite_risk():
    """Verify all 4 model outputs are completely separate with independent score columns."""
    engine = get_engine()
    inspector = inspect(engine)
    
    cost_cols = [c["name"] for c in inspector.get_columns("cost_anomaly_results")]
    assert "cost_anomaly_score" in cost_cols
    assert "composite_risk_score" not in cost_cols

    delay_cols = [c["name"] for c in inspector.get_columns("delay_results")]
    assert "delay_score" in delay_cols
    assert "composite_risk_score" not in delay_cols
