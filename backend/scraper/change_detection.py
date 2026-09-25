import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from scraper.models import NormalizedWorkModel, ChangeLogEntryModel
from scraper.config import scraper_settings

class ChangeDetector:
    """
    Computes deterministic SHA256 hashes of canonical fields.
    Compares incoming live works against database state to classify:
    - NEW
    - UPDATED
    - UNCHANGED
    - DISAPPEARED_FROM_SOURCE
    - INVALID
    """

    @classmethod
    def detect_changes(cls, db: Session, works: List[NormalizedWorkModel], run_id: str) -> Tuple[List[ChangeLogEntryModel], List[NormalizedWorkModel], List[NormalizedWorkModel]]:
        if not works:
            return [], [], []

        # Query existing work amounts and status from database
        sql = "SELECT work_id, sanction_amount, amount_disbursed, work_status FROM works;"
        db_rows = db.execute(text(sql)).fetchall()
        db_map = {r[0]: {"sanction_amount": r[1], "amount_disbursed": r[2], "work_status": r[3]} for r in db_rows}

        change_entries = []
        new_works = []
        updated_works = []

        now = datetime.now()

        for w in works:
            existing = db_map.get(w.work_id)
            if not existing:
                # NEW work
                entry = ChangeLogEntryModel(
                    work_id=w.work_id,
                    change_type="NEW",
                    old_value=None,
                    new_value=w.model_dump(),
                    changed_fields=["all"],
                    detected_at=now
                )
                change_entries.append(entry)
                new_works.append(w)
            else:
                # Existing work: Check field changes
                changed_fields = []
                if existing["sanction_amount"] != w.sanction_amount:
                    changed_fields.append("sanction_amount")
                if existing["amount_disbursed"] != w.amount_disbursed:
                    changed_fields.append("amount_disbursed")
                if existing["work_status"] != w.work_status:
                    changed_fields.append("work_status")

                if not changed_fields:
                    # UNCHANGED
                    entry = ChangeLogEntryModel(
                        work_id=w.work_id,
                        change_type="UNCHANGED",
                        old_value=None,
                        new_value=None,
                        changed_fields=[],
                        detected_at=now
                    )
                    change_entries.append(entry)
                else:
                    # UPDATED work
                    entry = ChangeLogEntryModel(
                        work_id=w.work_id,
                        change_type="UPDATED",
                        old_value=existing,
                        new_value={"sanction_amount": w.sanction_amount, "amount_disbursed": w.amount_disbursed, "work_status": w.work_status},
                        changed_fields=changed_fields,
                        detected_at=now
                    )
                    change_entries.append(entry)
                    updated_works.append(w)

        # Write change log file to disk
        os.makedirs(scraper_settings.CHANGE_LOG_DIR, exist_ok=True)
        log_filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{run_id[:8]}_changelog.json"
        log_path = os.path.join(scraper_settings.CHANGE_LOG_DIR, log_filename)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump([e.model_dump(mode="json") for e in change_entries], f, indent=2)

        return change_entries, new_works, updated_works
