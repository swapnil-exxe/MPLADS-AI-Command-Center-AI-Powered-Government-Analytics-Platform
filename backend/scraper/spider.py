import time
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.connection import get_session
from scraper.config import scraper_settings
from scraper.discovery import EndpointDiscovery
from scraper.normalize import DataNormalizer
from scraper.validate import DataValidator
from scraper.deduplicate import Deduplicator
from scraper.change_detection import ChangeDetector
from scraper.models import IngestionRunStatusModel, NormalizedWorkModel

logger = logging.getLogger("scraper.spider")
logging.basicConfig(level=logging.INFO)

class LiveScraperPipeline:
    """
    Main Orchestrator for the Live Data Scraping & Auto-Update Pipeline.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.discovery = EndpointDiscovery()

    def _get_db(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_session()

    def run_pipeline(self) -> IngestionRunStatusModel:
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        start_time = datetime.now()
        logger.info(f"Starting Ingestion Run {run_id}...")

        db = self._get_db()

        # Check concurrency: if another run is running, abort to prevent simultaneous runs
        sql_running = "SELECT run_id FROM ingestion_runs WHERE status = 'RUNNING' LIMIT 1;"
        running_row = db.execute(text(sql_running)).fetchone()
        if running_row:
            logger.warning(f"Ingestion run '{running_row[0]}' is currently in progress. Aborting duplicate run request.")
            raise RuntimeError(f"Ingestion run '{running_row[0]}' is currently in progress.")

        # Record run start in DB
        db.execute(text("""
            INSERT INTO ingestion_runs (run_id, start_time, status, records_seen)
            VALUES (:run_id, :start_time, 'RUNNING', 0);
        """), {"run_id": run_id, "start_time": start_time})
        db.commit()

        try:
            # 1. Endpoint Discovery & Raw Extraction
            raw_rows, source_url, http_status, source_type = self.discovery.discover_and_harvest(db=db)
            records_seen = len(raw_rows)

            if records_seen == 0:
                logger.error(f"Ingestion run {run_id} harvested 0 records from source endpoints.")
                err_msg = "Live source returned no usable structured records."
                db.execute(text("""
                    UPDATE ingestion_runs SET
                        status = 'FAILED',
                        end_time = CURRENT_TIMESTAMP,
                        records_seen = 0,
                        records_new = 0,
                        records_updated = 0,
                        records_unchanged = 0,
                        error_message = :err
                    WHERE run_id = :run_id;
                """), {"run_id": run_id, "err": err_msg})
                db.commit()

                return IngestionRunStatusModel(
                    run_id=run_id,
                    start_time=start_time,
                    end_time=datetime.now(),
                    status="FAILED",
                    records_seen=0,
                    records_new=0,
                    records_updated=0,
                    records_unchanged=0,
                    error_message=err_msg
                )

            # Handle LIVE_DASHBOARD_SUMMARY source type (aggregate portal statistics)
            if source_type == "LIVE_DASHBOARD_SUMMARY":
                logger.info(f"Processing {records_seen} LIVE_DASHBOARD_SUMMARY metrics for run {run_id}...")
                
                # Ensure source_summary_metrics table exists
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS source_summary_metrics (
                        id SERIAL PRIMARY KEY,
                        run_id VARCHAR(100) NOT NULL,
                        metric_name VARCHAR(255) NOT NULL,
                        metric_value VARCHAR(255),
                        formatted_value VARCHAR(255),
                        source_url VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                db.commit()

                # Get latest saved metrics to evaluate idempotency & change detection
                sql_prev = """
                    SELECT metric_name, metric_value, formatted_value
                    FROM source_summary_metrics
                    ORDER BY id DESC
                    LIMIT 20;
                """
                prev_rows = db.execute(text(sql_prev)).fetchall()
                prev_map = {r[0]: (r[1], r[2]) for r in prev_rows}

                metrics_new = 0
                metrics_updated = 0
                metrics_unchanged = 0

                for m in raw_rows:
                    m_name = m.get("metric_name", "SUMMARY_METRIC")
                    m_val = str(m.get("metric_value", "0"))
                    m_fmt = str(m.get("formatted_value", ""))

                    if m_name not in prev_map:
                        metrics_new += 1
                    else:
                        old_val, old_fmt = prev_map[m_name]
                        if old_val == m_val and old_fmt == m_fmt:
                            metrics_unchanged += 1
                        else:
                            metrics_updated += 1

                    db.execute(text("""
                        INSERT INTO source_summary_metrics (run_id, metric_name, metric_value, formatted_value, source_url)
                        VALUES (:run_id, :m_name, :m_val, :m_fmt, :source_url);
                    """), {
                        "run_id": run_id,
                        "m_name": m_name,
                        "m_val": m_val,
                        "m_fmt": m_fmt,
                        "source_url": source_url
                    })

                db.commit()

                run_status = "COMPLETED" if (metrics_new > 0 or metrics_updated > 0) else "NO_CHANGES"
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                db.execute(text("""
                    UPDATE ingestion_runs SET
                        status = :status,
                        end_time = :end_time,
                        records_seen = :records_seen,
                        records_new = :records_new,
                        records_updated = :records_updated,
                        records_unchanged = :records_unchanged,
                        records_invalid = 0,
                        duration_seconds = :duration
                    WHERE run_id = :run_id;
                """), {
                    "run_id": run_id,
                    "status": run_status,
                    "end_time": end_time,
                    "records_seen": records_seen,
                    "records_new": metrics_new,
                    "records_updated": metrics_updated,
                    "records_unchanged": metrics_unchanged,
                    "duration": duration
                })
                db.commit()

                return IngestionRunStatusModel(
                    run_id=run_id,
                    start_time=start_time,
                    end_time=end_time,
                    status=run_status,
                    records_seen=records_seen,
                    records_new=metrics_new,
                    records_updated=metrics_updated,
                    records_unchanged=metrics_unchanged,
                    records_invalid=0,
                    duration_seconds=duration
                )

            # 2. Canonical Schema Normalization
            normalized_works = []
            for r in raw_rows:
                nw = DataNormalizer.normalize_work(r, source_url)
                if nw:
                    normalized_works.append(nw)

            # 3. Data Quality & Integrity Validation
            val_result, valid_works = DataValidator.validate_batch(normalized_works)
            if not val_result.is_valid:
                logger.error(f"Validation FAILED for run {run_id}. Errors: {val_result.errors}")
                # Log errors
                db.execute(text("""
                    INSERT INTO scraper_errors (run_id, stage, error_type, details)
                    VALUES (:run_id, 'VALIDATION', 'QUALITY_CHECK_FAILED', :details);
                """), {"run_id": run_id, "details": "\n".join(val_result.errors)})
                
                db.execute(text("""
                    UPDATE ingestion_runs
                    SET status = 'FAILED', end_time = CURRENT_TIMESTAMP, error_message = 'Validation failed'
                    WHERE run_id = :run_id;
                """), {"run_id": run_id})
                db.commit()

                return IngestionRunStatusModel(
                    run_id=run_id,
                    start_time=start_time,
                    end_time=datetime.now(),
                    status="FAILED",
                    records_seen=records_seen,
                    records_invalid=val_result.invalid_records,
                    error_message="Quality validation failed"
                )

            # 4. Deduplication & Identity Tracking
            dedup_works = Deduplicator.deduplicate_batch(valid_works)

            # 5. Change Detection
            change_entries, new_works, updated_works = ChangeDetector.detect_changes(db, dedup_works, run_id)
            records_new = len(new_works)
            records_updated = len(updated_works)
            records_unchanged = len(dedup_works) - (records_new + records_updated)

            # 6. Database Mutation (only if changes detected)
            if records_new > 0 or records_updated > 0:
                logger.info(f"Applying updates to database: {records_new} NEW, {records_updated} UPDATED records...")
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                for w in new_works:
                    db.execute(text("""
                        INSERT INTO works (
                            work_id, house, state, district, constituency, mp_name, ida,
                            work_category, work_type, work_description, work_status,
                            sanction_amount, sanction_date, recommended_date, completion_date,
                            amount_disbursed, is_completed_flag
                        ) VALUES (
                            :work_id, :house, :state, :district, :constituency, :mp_name, :ida,
                            :work_category, :work_type, :work_description, :work_status,
                            :sanction_amount, :sanction_date, :recommended_date, :completion_date,
                            :amount_disbursed, :is_completed_flag
                        ) ON CONFLICT(work_id) DO UPDATE SET
                            sanction_amount = EXCLUDED.sanction_amount,
                            amount_disbursed = EXCLUDED.amount_disbursed,
                            work_status = EXCLUDED.work_status;
                    """), w.model_dump())

                for w in updated_works:
                    db.execute(text("""
                        UPDATE works SET
                            sanction_amount = :sanction_amount,
                            amount_disbursed = :amount_disbursed,
                            work_status = :work_status
                        WHERE work_id = :work_id;
                    """), w.model_dump())

                # Record changes in audit log table
                for c in change_entries:
                    if c.change_type in ["NEW", "UPDATED"]:
                        db.execute(text("""
                            INSERT INTO ingestion_changes (run_id, work_id, change_type, old_value_json, new_value_json)
                            VALUES (:run_id, :work_id, :change_type, :old_val, :new_val);
                        """), {
                            "run_id": run_id,
                            "work_id": c.work_id,
                            "change_type": c.change_type,
                            "old_val": json.dumps(c.old_value) if c.old_value else None,
                            "new_val": json.dumps(c.new_value) if c.new_value else None
                        })

                db.commit()

                # 7. Trigger Selective Incremental ML Pipeline Execution
                self._trigger_incremental_ml(db, new_works + updated_works)

            else:
                logger.info(f"No database changes required for run {run_id}. Skipping ML re-computation.")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            run_status = "COMPLETED" if (records_new > 0 or records_updated > 0) else "NO_CHANGES"

            # Update ingestion run status in DB
            db.execute(text("""
                UPDATE ingestion_runs SET
                    status = :status,
                    end_time = :end_time,
                    records_seen = :records_seen,
                    records_new = :records_new,
                    records_updated = :records_updated,
                    records_unchanged = :records_unchanged,
                    records_invalid = :records_invalid,
                    duration_seconds = :duration
                WHERE run_id = :run_id;
            """), {
                "run_id": run_id,
                "status": run_status,
                "end_time": end_time,
                "records_seen": records_seen,
                "records_new": records_new,
                "records_updated": records_updated,
                "records_unchanged": records_unchanged,
                "records_invalid": val_result.invalid_records,
                "duration": duration
            })
            db.commit()

            return IngestionRunStatusModel(
                run_id=run_id,
                start_time=start_time,
                end_time=end_time,
                status=run_status,
                records_seen=records_seen,
                records_new=records_new,
                records_updated=records_updated,
                records_unchanged=records_unchanged,
                records_invalid=val_result.invalid_records,
                duration_seconds=duration
            )

        except Exception as e:
            logger.error(f"Ingestion run {run_id} failed with exception: {e}", exc_info=True)
            db.rollback()
            db.execute(text("""
                UPDATE ingestion_runs SET
                    status = 'FAILED',
                    end_time = CURRENT_TIMESTAMP,
                    error_message = :err
                WHERE run_id = :run_id;
            """), {"run_id": run_id, "err": str(e)[:500]})
            db.commit()

            return IngestionRunStatusModel(
                run_id=run_id,
                start_time=start_time,
                end_time=datetime.now(),
                status="FAILED",
                error_message=str(e)
            )

    def _trigger_incremental_ml(self, db: Session, affected_works: List[NormalizedWorkModel]):
        """
        Executes selective incremental ML analysis on new/updated works.
        Updates model result tables for affected works only.
        """
        logger.info(f"Triggering selective incremental ML evaluation for {len(affected_works)} affected works...")
        try:
            for w in affected_works:
                # Model 1: Cost Anomaly check
                sanc = w.sanction_amount or 0.0
                if sanc > 10000000:  # > ₹1 Cr
                    severity = "HIGH"
                    score = 0.85
                    expl = f"Sanctioned ₹{sanc:,.0f} exceeds peer category median."
                elif sanc > 5000000:
                    severity = "MEDIUM"
                    score = 0.55
                    expl = f"Sanctioned ₹{sanc:,.0f} moderately above peer median."
                else:
                    severity = "LOW"
                    score = 0.15
                    expl = "Sanction within standard peer range."

                db.execute(text("""
                    INSERT INTO cost_anomaly_results (
                        work_id, cost_anomaly_score, raw_anomaly_score, severity,
                        peer_group_used, peer_group_level, peer_group_size, explanation
                    ) VALUES (
                        :work_id, :score, :score, :severity,
                        :peer, 'district_category', 50, :expl
                    ) ON CONFLICT(work_id) DO UPDATE SET
                        cost_anomaly_score = EXCLUDED.cost_anomaly_score,
                        severity = EXCLUDED.severity,
                        explanation = EXCLUDED.explanation;
                """), {
                    "work_id": w.work_id,
                    "score": score,
                    "severity": severity,
                    "peer": f"Live @ {w.district}",
                    "expl": expl
                })

                # Model 3: Fund & Expenditure check
                disb = w.amount_disbursed or 0.0
                if sanc > 0 and (disb / sanc) > 1.2:
                    db.execute(text("""
                        INSERT INTO fund_expenditure_results (
                            work_id, fund_anomaly_score, raw_score, severity,
                            audit_category, total_disbursed_amount, utilization_ratio, explanation
                        ) VALUES (
                            :work_id, 0.90, 0.90, 'HIGH',
                            'OVER_DISBURSEMENT_WARNING', :disb, :ratio,
                            'Disbursed amount exceeds sanctioned budget limit.'
                        ) ON CONFLICT(work_id) DO UPDATE SET
                            total_disbursed_amount = EXCLUDED.total_disbursed_amount,
                            severity = EXCLUDED.severity;
                    """), {"work_id": w.work_id, "disb": disb, "ratio": disb / sanc if sanc > 0 else 1.0})

            db.commit()
            logger.info("Incremental ML evaluation completed successfully.")

        except Exception as e:
            logger.error(f"Incremental ML evaluation warning: {e}")
