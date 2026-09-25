# 02. Complete System Architecture

## Complete Layered Architecture

The MPLADS AI Command Center is designed as a decoupled, multi-tiered enterprise architecture:

```
[ Client Layer (React 18 SPA + Vite + Tailwind) ]
                     │
                     ▼ HTTP REST / OAuth2 JWT
[ FastAPI Application Gateway (Uvicorn ASGI) ]
   ├── Authentication & Timing Defense (Bcrypt 12-round)
   ├── Rate Limiting (SlowAPI: 5/min login, 120/min general)
   └── Server-Side RBAC Scoping (Predicate Injection)
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
 [ Supabase DB ]  [ Analytics ] [ Groq LLM ]
 PostgreSQL 17.6   Parquet Core  Subho AI
```

---

## Detailed System Component Responsibilities

### 1. Data Ingestion & Scraper Tier (`scraper/`, `data_pipeline/`)
- **Scraper Spider (`scraper/spider.py`)**: Crawls government portal endpoints asynchronously, storing source snapshots.
- **SHA-256 Hash Change Detection (`scraper/change_detection.py`)**: Computes SHA-256 content hashes of raw responses to track new, updated, and unchanged records.
- **Pipeline Cleaners (`data_pipeline/cleaners.py`)**: Sanitizes raw strings, strips tab characters (`\t`), parses Indian currency values, and normalizes mixed date formats to ISO `YYYY-MM-DD`.

### 2. Analytical Core Tier (`ml_models/`, `rule_engines/`)
- Executes 4 strictly independent analytical engines:
  - **Model 1**: Cost Anomaly Isolation Forest (`ml_models/cost_anomaly/`)
  - **Model 2**: Duplicate Work Sentence Transformer (`ml_models/duplicate_work/`)
  - **Model 3**: Fund Expenditure Isolation Forest (`ml_models/fund_expenditure_anomaly/`)
  - **Phase 5 Engine**: Statutory SLA Delay Rule Engine (`rule_engines/delay/`)

### 3. Database Tier (`database/`)
- **Supabase PostgreSQL 17.6**: Primary production cloud relational database storing master catalog `works`, outputs (`cost_anomaly_results`, `duplicate_work_results`, `fund_expenditure_results`, `delay_results`), `work_expenditures`, and `users`.
- **SQLite (`mplads_master.db`)**: Local development and offline testing fallback.
- **Parquet Storage (`data/model_outputs/`)**: High-performance columnar storage for fast offline analytics and training.

### 4. API & Application Gateway Tier (`api/`)
- **FastAPI Framework**: ASGI application handling REST endpoints, OpenAPI documentation, and SPA routing.
- **Security & RBAC (`api/auth/`)**: Validates JWT signatures, re-verifies user active status in PostgreSQL, and injects jurisdictional WHERE predicates based on the caller's role (`MINISTRY`, `STATE_OFFICER`, `DISTRICT_OFFICER`, `MP`).

### 5. Presentation & User Experience Tier (`frontend/`)
- **React 18 SPA**: Built with Vite and TypeScript, featuring dark command-center UI, responsive navigation, dynamic Recharts visualizations, interactive maps, and Subho AI Chatbot widget.

