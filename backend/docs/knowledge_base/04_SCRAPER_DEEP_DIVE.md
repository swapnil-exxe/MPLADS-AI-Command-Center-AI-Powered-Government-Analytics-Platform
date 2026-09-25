# 04. Live Scraper Engine Deep Dive

## Live Scraper Engine Architecture (`scraper/`)

The scraper package is a resilient, asynchronous crawling system designed to extract live data from the official MPLADS portal:

### Key Components

1. **Async Spider (`scraper/spider.py`)**: Asynchronously requests portal pages, managing connection pooling and retries.
2. **HTML & JSON Parsers (`scraper/parsers/`)**: Dedicated parsing modules for works, financial vouchers, and MP profiles (`works.py`, `financials.py`, `mp.py`).
3. **SHA-256 Change Detection (`scraper/change_detection.py`)**: Computes SHA-256 hashes of incoming responses to detect whether a record is `NEW`, `UPDATED`, or `UNCHANGED`.
4. **Ingestion Logging (`database/models.py`)**: Persists execution metadata across four database tables:
   - `source_snapshots`: Raw HTML/JSON response hashes and status codes.
   - `ingestion_runs`: Execution start/end timestamps, duration, and record counts.
   - `ingestion_changes`: Field-level diff audit logs (`old_value_json` vs `new_value_json`).
   - `scraper_errors`: Error stage, type, and stacktrace details.

---

## Change Detection Workflow

```
Fetch Web Response -> Compute SHA-256 Hash -> Compare with source_snapshots DB Table
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
          Hash Match                     Hash Mismatch / New URL
      (Status: UNCHANGED)               (Parse Content & Compare Fields)
                 │                               │
                 ▼                               ▼
         Skip Database Write              Log IngestionChange Diff & Update DB
```

