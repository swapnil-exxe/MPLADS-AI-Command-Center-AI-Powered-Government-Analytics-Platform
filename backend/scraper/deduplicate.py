from typing import List, Dict, Any, Tuple
from scraper.models import NormalizedWorkModel

class Deduplicator:
    """
    Deduplicates incoming works using primary key identity `source + work_id`.
    Maintains record versioning and lineage attributes.
    """

    @staticmethod
    def deduplicate_batch(works: List[NormalizedWorkModel]) -> List[NormalizedWorkModel]:
        seen = {}
        for w in works:
            key = f"{w.source_dataset}::{w.work_id.strip()}"
            if key not in seen:
                seen[key] = w
            else:
                # Keep latest/most complete work representation
                existing = seen[key]
                if w.sanction_amount is not None and existing.sanction_amount is None:
                    seen[key] = w
                elif w.amount_disbursed is not None and existing.amount_disbursed is None:
                    seen[key] = w

        return list(seen.values())
