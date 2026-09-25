import os
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from sqlalchemy import text
from scraper.config import scraper_settings
from scraper.models import RawSnapshotModel

class SnapshotManager:
    """
    Manages immutable raw snapshot storage for historical auditing & reproducibility.
    Path structure: data/raw/live_source/YYYY/MM/DD/timestamp/
    """

    @staticmethod
    def create_snapshot(source_url: str, raw_content: Any, http_status: int = 200, db: Optional[Any] = None) -> Tuple[RawSnapshotModel, str]:
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        ts = now.strftime("%H%M%S")

        snapshot_dir = os.path.join(
            scraper_settings.RAW_SNAPSHOT_DIR, year, month, day, ts
        )
        os.makedirs(snapshot_dir, exist_ok=True)

        if isinstance(raw_content, (dict, list)):
            content_str = json.dumps(raw_content, indent=2, ensure_ascii=False)
            filename = "raw_payload.json"
        else:
            content_str = str(raw_content)
            filename = "raw_response.html"

        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
        file_path = os.path.join(snapshot_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)

        # Save metadata
        snapshot_id = f"snap_{year}{month}{day}_{ts}_{content_hash[:8]}"
        records_extracted = len(raw_content) if isinstance(raw_content, list) else (1 if raw_content else 0)

        meta = {
            "snapshot_id": snapshot_id,
            "snapshot_path": file_path,
            "source_url": source_url,
            "http_status": http_status,
            "content_hash": content_hash,
            "records_extracted": records_extracted,
            "created_at": now.isoformat()
        }

        meta_path = os.path.join(snapshot_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        if db is not None:
            try:
                db.execute(text("""
                    INSERT INTO source_snapshots (id, snapshot_path, source_url, http_status, content_hash, records_extracted, created_at)
                    VALUES (:id, :path, :url, :status, :hash, :count, :created_at)
                    ON CONFLICT (id) DO NOTHING;
                """), {
                    "id": snapshot_id,
                    "path": file_path,
                    "url": source_url,
                    "status": http_status,
                    "hash": content_hash,
                    "count": records_extracted,
                    "created_at": now
                })
                db.commit()
            except Exception as e:
                db.rollback()

        snapshot_model = RawSnapshotModel(
            snapshot_id=snapshot_id,
            snapshot_path=file_path,
            source_url=source_url,
            http_status=http_status,
            content_hash=content_hash,
            records_extracted=records_extracted,
            created_at=now
        )

        return snapshot_model, file_path
