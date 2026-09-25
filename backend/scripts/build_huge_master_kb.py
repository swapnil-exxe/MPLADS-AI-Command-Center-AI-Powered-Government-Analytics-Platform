import os
from pathlib import Path

root_dir = Path("/Users/swapnil/Documents/PS102")
docs_dir = root_dir / "docs"
master_file = root_dir / "PROJECT_COMPLETE_TECHNICAL_KNOWLEDGE_BASE.md"
docs_master_file = docs_dir / "PROJECT_COMPLETE_TECHNICAL_KNOWLEDGE_BASE.md"

full_text = r"""# MPLADS AI Command Center — Master Project Technical Knowledge Base & Complete Viva Reference

> **System**: AI-Powered MPLADS Analytics & Governance Platform  
> **Repository**: [`https://github.com/swapnil-exxe/MPLADS-AI-Command-Center-AI-Powered-Government-Analytics-Platform.git`](https://github.com/swapnil-exxe/MPLADS-AI-Command-Center-AI-Powered-Government-Analytics-Platform.git)  
> **Dataset Scope**: 190,942 Master Works | 109,311 Expenditure Vouchers | ₹10,211.49 Cr Sanctioned Outlay | 773 Districts | 36 States  
> **Validation**: 117/117 Automated Tests Passing (100% Pass Rate) | 0 Critical Vulnerabilities  

---

# Module 01: Problem Statement & Solution Overview

## Executive Overview & Real-World Context

The **Members of Parliament Local Area Development Scheme (MPLADS)** is a flagship Central Sector Scheme fully funded by the Government of India. Under this scheme, each Member of Parliament (MP) has the entitlement to recommend developmental works in their constituency costing up to **₹5 Crore per annum**, focusing primarily on creating durable community assets such as drinking water systems, primary health centers, rural roads, public libraries, school infrastructure, and sanitation facilities.

With **788 MPs** across both houses of Parliament (Lok Sabha and Rajya Sabha), over **₹3,900 Crore** is allocated annually for public assets across **36 States/UTs** and **773 Districts**. Across multiple parliamentary terms, this results in over **190,000 active and historical works** worth over **₹10,211 Crore**.

---

## The Core Governance Challenge

Monitoring government asset creation across 773 districts presents massive systemic hurdles:

1. **Massive Scale & Volume**: Manually reviewing 190,942 individual work recommendations, sanction orders, and 109,311 payment vouchers across 773 districts is physically impossible for human vigilance officers.
2. **Cost Overruns & Inflated Estimates**: Due to fragmented local tenders, sanction costs for identical works (e.g. *Installation of 50W Solar Street Light*) vary by 10x to 25x across adjacent districts or states without triggering red flags.
3. **Duplicate Work Sanctions & Double Billing**: Identical or overlapping physical projects (e.g., *Community Hall Construction*) are frequently sanctioned and billed multiple times under slightly altered names across consecutive years, adjacent boundaries, or different MPs.
4. **Financial Bottlenecks & Voucher Discrepancies**: Funds sit unutilized for years after sanction, or completed projects reflect 0 expenditure vouchers on portal records due to administrative reporting lag.
5. **Severe Statutory SLA Delays**: Over 51% of recommended works breach Para 3.12 of the official MPLADS Guidelines, which mandates that District Authorities accord sanction within **75 days** of receiving an MP recommendation.

---

## Pitch Versions for Stakeholders & Evaluators

### 1. One-Line Problem Statement
> *“Manual oversight fails at scale across 190,000+ distributed public works, enabling cost inflation, duplicate billing, dormant funds, and severe statutory SLA breaches.”*

### 2. 30-Second Elevator Pitch
> *“Under the MPLAD Scheme, MPs allocate ₹5 Crore annually for local infrastructure across 773 districts. Because monitoring nearly 200,000 works manually is impossible, millions of rupees are lost to inflated estimates, duplicate project billing, dormant allocations, and years of bureaucratic delay. We built the MPLADS AI Command Center — an end-to-end analytics platform powered by 4 independent ML and Rule engines that automatically audits every work for cost anomalies, semantic duplicates, fund irregularities, and statutory delay SLA breaches in real-time.”*

### 3. 2-Minute Presentation Pitch
> *“India’s MPLAD Scheme funds thousands of vital community assets every year. However, central and state authorities face a massive data dark-spot: 190,942 works worth over ₹10,200 Crore are recorded across fragmented portal dumps. Human vigilance teams cannot detect when a school hall in Bihar is sanctioned at 15 times the median state cost, or when two identical road repair projects are billed under different titles in the same district.*
>
> *Our solution, the MPLADS AI Command Center, transforms raw portal dumps into actionable governance intelligence. First, an automated ingestion scraper normalizes raw records into a canonical dataset. Next, four dedicated analytical engines evaluate each work independently:*
> *1. A Hierarchical Peer-Grouped Isolation Forest detects inflated cost estimates at sanction time with zero data leakage.*
> *2. A Transformer-based Sentence-BERT model combined with structural proximity signals detects duplicate work candidate pairs.*
> *3. A Multivariate Expenditure Isolation Forest flags voucher concentration anomalies and status-expenditure mismatches.*
> *4. A Statutory Rule Engine enforces the official 75-day sanction SLA and 365-day execution guidelines.*
>
> *Finally, an enterprise FastAPI gateway and React 18 command-center dashboard present role-scoped risk dossiers to Central Ministry, State, District, and MP stakeholders, complete with an AI assistant for natural-language inquiry.”*

### 4. Detailed Technical Problem Statement
> *“To design, implement, and validate an automated, scalable data-processing and machine-learning governance platform capable of ingesting heterogeneous administrative records of the MPLADS scheme, normalizing currency, date, and text fields into a canonical schema of 190,942 works, engineering domain-specific feature registries, executing four strictly independent anomaly and compliance models (Cost Anomaly Isolation Forest, Sentence-Transformer Duplicate Matcher, Expenditure Cohort Isolation Forest, and Statutory SLA Rule Engine), storing results in a cloud PostgreSQL database with strict Row Level Security, and exposing server-side RBAC-scoped REST APIs to a responsive React command-center interface.”*

---

## Exactly What WE Built — Solution Architecture

The **MPLADS AI Command Center** is an integrated governance analytics platform consisting of:

- **Live Data Scraper (`scraper/`)**: Automated crawler utilizing Scrapling and Async HTTP to ingest raw portal dumps, compute SHA-256 content hashes, track change logs, and log ingestion runs.
- **Canonical Feature Pipeline (`data_pipeline/`, `feature_engineering/`)**: Cleaners that standardize Indian currency (`₹`), ISO dates, and tab control characters, unifying 190,942 works and 109,311 vouchers.
- **4 Independent Analytical Core Engines**:
  - **Model 1: Cost Anomaly Detector (`ml_models/cost_anomaly/`)**: Peer-grouped Isolation Forest benchmarking cost estimates against state/national work medians.
  - **Model 2: Duplicate Work Detector (`ml_models/duplicate_work/`)**: `all-MiniLM-L6-v2` dense embeddings (384-d) combined with structural proximity scoring across a 90-day candidate blocking window.
  - **Model 3: Fund Anomaly Detector (`ml_models/fund_expenditure_anomaly/`)**: Isolation Forest on active spenders + Herfindahl-Hirschman Index (HHI) payment concentration + deterministic status mismatch rules.
  - **Phase 5: Delay Rule Engine (`rule_engines/delay/`)**: Statutory SLA rule engine enforcing 75-day sanction limits and 365-day work completion windows against a fixed reference date (`2026-09-05`).
- **Supabase PostgreSQL 17.6 Relational Core (`database/`)**: Cloud database enforcing zero orphaned foreign keys and Row Level Security.
- **FastAPI Application Gateway (`api/`)**: OAuth2 Bearer JWT authentication, Bcrypt 12-round hashing with constant-time dummy timing attack mitigation, and server-side SQL predicate injection for 4 governance tiers (`MINISTRY`, `STATE_OFFICER`, `DISTRICT_OFFICER`, `MP`).
- **React 18 Command Center SPA (`frontend/`)**: Vite, TypeScript, Tailwind CSS, Recharts, interactive district/MP summaries, work dossiers, and Subho AI chatbot powered by Groq LLM candidate fallback chains.

---

## Feature-by-Feature Micro Breakdown

| Feature | WHAT? | WHY? | HOW? | INPUT | PROCESS | OUTPUT | WHO USES IT? |
|---|---|---|---|---|---|---|---|
| **Cost Anomaly Audit** | Detects inflated cost estimates. | Prevents tender price padding. | Peer Isolation Forest. | Sanction amount, work type, state. | Hierarchical median IQR & Isolation Forest score. | Calibrated Score `[0,1]`, Severity (`HIGH/MED/LOW`). | District Officers & Ministry. |
| **Duplicate Work Matcher** | Flags double-billed projects. | Stops double funding. | Sentence-BERT + Structural scoring. | Work description, date, amount, location. | Candidate blocking (90d) + MiniLM-L6-v2 cosine similarity. | Candidate pairs with similarity score & reasons. | Vigilance Officers & State Nodal Authorities. |
| **Fund Anomaly Monitor** | Identifies payment irregularities. | Prevents voucher fraud & dormant funds. | Cohort Isolation Forest & HHI. | Voucher amounts, dates, work status. | Active spend HHI calculation & Status mismatch check. | Audit category, HHI score, anomaly reasons. | Ministry & District Planning Officers. |
| **Statutory Delay Tracker** | Measures SLA compliance. | Enforces legal timelines. | Rule Engine (Para 3.12). | Recommendation, sanction, completion dates. | SLA difference vs 75d & 365d limits against `2026-09-05`. | Delay score, primary delay type, overdue days. | MPs & State Officers. |
| **Subho AI Chatbot** | Conversational query interface. | Instant natural-language insights. | Groq LLM API + Context injection. | User prompt + scoped DB metrics. | Prompt injection filter + Role system prompt + Groq LLM fallback chain. | Natural language response with suggestions. | All Stakeholder Roles. |

---

# Module 02: Complete System Architecture

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

---

# Module 03: Data Pipeline & Dataset Lineage

## Data Lineage & Lifecycle

Data in the MPLADS AI Command Center follows a strictly linear, auditable pipeline from raw portal dumps to frontend visualizations:

```
Raw Portal CSVs (Lok Sabha 18th & Rajya Sabha Sitting)
                    │
                    ▼
Data Pipeline Ingestion & Normalization (`data_pipeline/`)
- Currency Parsing (₹ -> Numeric)
- ISO Date Normalization (DD/MM/YYYY -> YYYY-MM-DD)
- Tab & Control Character Scrubbing
                    │
                    ▼
Canonical Master Works Layer (`canonical_works.parquet` - 190,942 records)
                    │
                    ├───> Model 1: Cost Anomaly Detector (Hierarchical Peer Isolation Forest)
                    ├───> Model 2: Duplicate Work Detector (MiniLM-L6-v2 + Candidate Blocking)
                    ├───> Model 3: Fund Anomaly Detector (Active Spend Isolation Forest + HHI)
                    └───> Phase 5: Delay SLA Rule Engine (75d Sanction & 365d Completion SLAs)
                    │
                    ▼
Supabase PostgreSQL 17.6 Relational Database (`database/`)
- master catalog: `works` (190,942 rows)
- expenditures: `work_expenditures` (109,311 rows)
- model results: `cost_anomaly_results`, `duplicate_work_results`, `fund_expenditure_results`, `delay_results`
                    │
                    ▼
FastAPI Application Gateway & RBAC Scoping (`api/`)
                    │
                    ▼
React 18 SPA Command Center (`frontend/`)
```

---

## Dataset Statistics & Coverage

- **Total Master Works**: **190,942**
- **Total Expenditure Vouchers**: **109,311**
- **States / Union Territories Covered**: **36**
- **Districts Covered**: **773**
- **Total Sanctioned Outlay**: **₹10,211.49 Crore**
- **Total Disbursed Capital**: **₹10,166.10 Crore**
- **Overall Fund Utilization Rate**: **99.56%**

---

# Module 04: Live Scraper Engine Deep Dive

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

---

# Module 05: Database Architecture & ER Deep Dive

## Dual-Database & Analytical Parquet Architecture

The platform employs a hybrid database strategy tailored for distinct operational environments:

### 1. Production Relational Core — Supabase PostgreSQL 17.6
- **Role**: Primary cloud database hosting live web applications.
- **Security**: Row Level Security (RLS) enabled on all 7 core tables.
- **Connection**: Pooled connection via SQLAlchemy with SSL.
- **Integrity**: Enforces 0 orphaned foreign keys across all analytical result tables.

### 2. Local Fallback Database — SQLite (`mplads_master.db`)
- **Role**: Lightweight offline development and testing fallback.
- **Configuration**: Automatically configured by `database/connection.py` when `USE_LOCAL_SQLITE=true`.

### 3. Vectorized Analytical Storage — Apache Parquet (`data/model_outputs/`)
- **Role**: High-speed columnar files used by Python ML libraries (Pandas/Polars/PyArrow) for offline training and vectorized feature computation.

---

## Core Database Tables

- `works`: Master catalog of 190,942 works.
- `cost_anomaly_results`: Model 1 peer Isolation Forest scores and severities.
- `duplicate_work_results`: Model 2 candidate duplicate pairs and structural scores.
- `fund_expenditure_results`: Model 3 expenditure anomaly scores and HHI ratios.
- `delay_results`: Phase 5 statutory SLA delay scores and primary delay types.
- `work_expenditures`: 109,311 payment vouchers linked to works via foreign key.
- `users`: Stakeholder accounts and jurisdictional scope definitions.

---

# Module 06: Analytical & Machine Learning Core Models

The platform strictly avoids artificial risk score averaging. Each model evaluates a distinct compliance dimension:

---

### Model 1: Cost Anomaly Detector (`ml_models/cost_anomaly/`)
- **Purpose**: Evaluates cost estimate reasonableness at sanction time.
- **Zero-Leakage**: Uses 0 post-sanction features.
- **Hierarchical Peer Grouping**:
  1. `STATE_WORK_TYPE` (Primary, >95% works)
  2. `NATIONAL_WORK_TYPE` (Fallback for peer count < 15)
  3. `NATIONAL_OVERALL` (Emergency fallback for peer count < 15)
- **Algorithm**: Peer-trained Isolation Forest (`n_estimators=100`, `contamination=0.01`). Raw output mapped to `[0,1]` via calibrated Sigmoid transformation.

---

### Model 2: Duplicate Work Detector (`ml_models/duplicate_work/`)
- **Purpose**: Identifies potential duplicate project sanctions.
- **Candidate Blocking**: 90-day sanction date window within identical state and category (reduces pairwise checks from 4.88B to 2.02M).
- **Embedding Transformer**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Scoring Formula**:
  $$\text{duplicate\_score} = 0.65 \times \text{semantic\_similarity} + 0.35 \times \text{structural\_score}$$
  Where structural score combines amount similarity, date proximity, same MP, and same constituency flags.

---

### Model 3: Fund & Expenditure Anomaly Detector (`ml_models/fund_expenditure_anomaly/`)
- **Purpose**: Monitors payment concentration, velocity, and status mismatches.
- **Cohorts**:
  - Active Spenders (Disbursed > 0): Isolation Forest trained on 6 features including Herfindahl-Hirschman Index (HHI) voucher concentration.
  - Zero-Disbursement (Disbursed = 0): Deterministic rules flagging dormant sanctions (>365d old) and status-expenditure mismatches (marked complete but 0 vouchers).

---

### Phase 5: Delay & Statutory SLA Rule Engine (`rule_engines/delay/`)
- **Purpose**: Enforces statutory timelines mandated by Para 3.12 of MPLADS Guidelines.
- **Track 1**: Recommendation to Sanction SLA (75-Day limit).
- **Track 2**: Sanction to Completion SLA (365-Day limit).
- **Track 3**: Open Work Aging evaluated against reference date `2026-09-05`.

---

# Module 07: Feature Engineering Registry

## Feature Engineering Pipeline (`feature_engineering/`)

The feature engineering registry converts raw portal records into clean analytical matrices:

### Core Feature Transformations

1. **Log Transformations**: `sanction_amount_log`, `log_disbursed_amount`, `days_to_first_disbursement_log` to eliminate monetary skewness.
2. **IQR Deviations**: Cost ratio vs peer group median and IQR deviation metrics.
3. **Herfindahl-Hirschman Index (HHI)**:
   $$\text{HHI} = \sum_{i=1}^{n} \left(\frac{\text{voucher\_amount}_i}{\text{total\_disbursed}}\right)^2$$
   Measures voucher disbursement concentration (1.0 = lump-sum single release, <0.2 = gradual phased tranches).
4. **Temporal Lag Vectors**: Elapsed days between recommendation, sanction, first voucher, last voucher, and completion.

---

# Module 08: Statutory SLA Rule Engine

## Statutory Delay SLA Rule Engine (`rule_engines/delay/`)

Statutory compliance in government schemes is a legal mandate, requiring a deterministic Rule Engine rather than a probabilistic ML model.

### SLA Thresholds & Severity Mapping

- **Sanction SLA (Para 3.12 - 75 Days)**:
  - $\le 75\text{ days}$: `NONE` (Compliant)
  - $76 - 150\text{ days}$: `LOW`
  - $151 - 225\text{ days}$: `MEDIUM`
  - $> 225\text{ days}$: `HIGH` (>3x legal limit)

- **Execution SLA (365 Days)**:
  - $\le 365\text{ days}$: `NONE` (Compliant)
  - $366 - 548\text{ days}$: `LOW`
  - $549 - 730\text{ days}$: `MEDIUM`
  - $> 730\text{ days}$: `HIGH` (>2 years elapsed)

- **Open Work Aging**:
  - Evaluates active elapsed days from sanction date to fixed reference date `2026-09-05`.

---

# Module 09: FastAPI Backend Application Gateway

## FastAPI Application Gateway Architecture (`api/`)

The backend gateway acts as the secure intermediary between governance clients and database storage.

### Core Configuration

- **Framework**: FastAPI (`fastapi>=0.115.0`) on ASGI server Uvicorn.
- **Middleware**: CORS middleware, SlowAPI rate limiter (5 req/min on login), process-time diagnostic header (`X-Process-Time-Ms`).
- **SPA Routing**: Mounts `/videos` and `/assets`, serving `frontend/dist/index.html` for unknown client-side routes.

### Primary Endpoint Categories

- `/api/v1/health`: Connection check and latencies.
- `/api/v1/auth/*`: Authentication, token generation, user profiles, user provisioning.
- `/api/v1/works/*`: Work list catalog and single-work dossiers.
- `/api/v1/analytics/*`: Model-specific detections (cost anomalies, duplicate pairs, fund anomalies, delays, district/MP summaries).
- `/api/v1/chat/*`: Subho AI chatbot query endpoints.

---

# Module 10: Authentication, RBAC & Security Architecture

## Cryptographic Security Stack
- **JWT Standard**: HMAC-SHA256 (`HS256`) signed tokens with 60-minute expiration.
- **Password Hashing**: Direct `bcrypt` with 12 rounds cost factor.

## Timing Attack Defense
To prevent username enumeration via response timing, `api/auth/security.py` executes a pre-computed 12-round dummy bcrypt hash check (`DUMMY_BCRYPT_HASH`) when an invalid email is submitted. This ensures uniform ~90ms response times for all login attempts.

---

## Server-Side RBAC & Jurisdictional Scoping

Jurisdictional access control is enforced at the database query level via **predicate injection**:

- **`MINISTRY`**: Unrestricted national scope across all 36 States.
- **`STATE_OFFICER`**: Injects `WHERE works.state = :user_state`.
- **`DISTRICT_OFFICER`**: Injects composite predicate `WHERE works.state = :user_state AND works.district = :user_district` (resolves 75 duplicate district names across India).
- **`MP`**: Injects `WHERE works.mp_name = :user_mp_name`.

---

## IDOR Protection Strategy

- **List Endpoints**: Scoped queries return empty sets (`items: []`) for out-of-jurisdiction filters.
- **Detail Endpoints (`/works/{id}`)**: Returns `404 Not Found` if the work ID does not exist, and `403 Forbidden` if the work ID exists but falls outside the caller's jurisdiction.

---

# Module 11: Frontend Command-Center UI/UX

## React 18 Single-Page Application (`frontend/`)

Built with React 18, Vite, TypeScript, Tailwind CSS, Recharts, and Lucide Icons.

### Key Pages & Dashboards

1. `LandingPage.tsx`: High-contrast public landing portal with hero video background, platform KPIs, and public chatbot.
2. `Login.tsx`: Authenticated gateway with video background and rate-limited credential form.
3. `Dashboard.tsx`: Executive command center with national metrics, active risk flags, and dynamic trend charts.
4. `WorksRegistry.tsx`: Filterable table of all 190,942 works with status badges and detail links.
5. `WorkDetail.tsx`: Single-work dossier displaying independent profiles for all 4 analytical models.
6. `CostAnomalies.tsx`, `DuplicateWorks.tsx`, `FundAnomalies.tsx`, `StatutoryDelays.tsx`: Dedicated module risk dashboards.
7. `MPSummary.tsx`, `DistrictSummary.tsx`: Jurisdictional portfolio pages for MPs and District Magistrates.

---

# Module 12: Subho AI Governance Chatbot

## Subho AI Governance Chatbot (`api/routers/chat.py`)

Subho AI is an interactive conversational assistant for platform users:

### Architecture & LLM Integration
- **LLM Engine**: Groq API caller with model fallback chain (`llama-3.3-70b-versatile`, `groq/compound`, `qwen/qwen3.6-27b`).
- **Prompt Injection Defense (`check_prompt_injection`)**: Regex pattern matching against prompt override attempts (`ignore previous instructions`, `gsk_*`, `postgresql://`).
- **Output Redaction (`sanitize_chat_output`)**: Regex filter redacting API keys, database connection strings, and JWT secrets before returning responses.
- **Context Injection**: Server-side injection of authorized jurisdictional metrics into LLM system prompts based on user role (`PUBLIC`, `MP`, `PARLIAMENT`, `ORGANIZATION`, `AGENCY`).

---

# Module 13: Comprehensive Automated Test Suite & QA

## Automated Test Suite Architecture (`tests/`)

The platform contains a test suite of **117 automated tests** across 15 test files with a **100% pass rate**:

### Test Suites Summary

- `test_api.py` (15 tests): Core REST API endpoints and dossiers.
- `test_auth_rbac.py` (19 tests): Login authentication, timing defense, JWT verification, and 4 stakeholder RBAC scopes.
- `test_database_ingestion.py` (6 tests): Database connections, table schemas, and foreign key integrity.
- `test_delay_rules.py` (7 tests): SLA thresholds (75d & 365d) and open work aging.
- `test_feature_engineering.py` (10 tests): Canonical building, zero leakage, and candidate blocking.
- `test_model1_cost_anomaly.py` (6 tests): Peer Group Isolation Forest scoring.
- `test_model2_duplicate_work.py` (6 tests): Sentence Transformer similarity scoring.
- `test_model3_fund_expenditure.py` (6 tests): Cohort Isolation Forest and HHI concentration.
- `test_pipeline.py` (10 tests): Currency, date, and string cleaners.
- `test_scraper.py` (4 tests): Spider requests and change detection.
- `test_subho_chatbot.py` (3 tests): Chatbot injection defenses and fallback responses.
- `test_trend_api.py` & `test_trend_rollups.py` (15 tests): Quarterly trend analytics.

---

# Module 14: Performance Optimization & Deployment Guide

## Performance Optimization & Deployment Architecture

### Performance Optimizations
1. **Database Indexing**: B-Tree composite indexes on `(state, district)`, `(work_id_1, work_id_2)`, `work_status`, and `severity`.
2. **Columnar Parquet Processing**: Offline model scoring uses Apache Parquet for fast memory-mapped vectorized Pandas operations.
3. **Frontend Bundle Single-File SPA**: Production bundle compiled to `frontend/dist/index.html` (1,003 kB), served directly by FastAPI.

### Deployment Workflow
- **Localhost Backend**: FastAPI / Uvicorn hosted locally at `http://127.0.0.1:8000/api/v1` connected to Supabase PostgreSQL over SSL.
- **Environment Isolation**: `.env` file isolated on server; `.env.example` committed to repo.

---

# Module 15: Complete Repository File Map

## Complete Workspace Directory & File Map

```
PS102/
├── .env.example              # Environment variables template
├── .gitattributes            # Standard git line endings config
├── .gitignore                # Exclusion rules for secrets, DB binaries, caches
├── README.md                 # Primary repository documentation
├── requirements.txt          # Python dependency specifications
├── PROJECT_STRUCTURE.md      # Workspace directory breakdown
├── FILE_ORGANIZATION_REPORT.md # File reorganization log
│
├── api/                      # FastAPI Backend Gateway
│   ├── config.py, dependencies.py, main.py
│   ├── auth/                 # Dependencies, limiter, scoping, security
│   ├── routers/              # 11 REST controllers
│   └── schemas/              # Pydantic v2 data models
│
├── database/                 # Relational Core
│   ├── connection.py, models.py, schema.sql, populate_sqlite.py, populate_supabase_direct.py
│
├── data_pipeline/            # Ingestion & Normalization
│   ├── amounts.py, cleaners.py, dates.py, geography.py, pipeline.py
│
├── feature_engineering/      # Feature Matrix Extraction
│   ├── canonical.py, duplicate_candidates.py, expenditure_features.py, work_features.py
│
├── ml_models/                # ML Detection Package
│   ├── cost_anomaly/, duplicate_work/, fund_expenditure_anomaly/
│
├── rule_engines/             # Statutory Rule Engine
│   └── delay/                # SLA delay evaluation
│
├── scraper/                  # Live Crawler Engine
│   ├── spider.py, client.py, change_detection.py, parsers/
│
├── scripts/                  # Production Orchestration
│   ├── run_full_ml_pipeline.py, build_canonical_dataset.py, verify_full_pipeline.py, security_audit.py
│
├── tests/                    # 117 Automated Tests
│   ├── test_api.py, test_auth_rbac.py, test_delay_rules.py, etc.
│
├── frontend/                 # React 18 SPA Application
│   ├── package.json, vite.config.ts, src/, public/
│
└── docs/                     # Documentation & Knowledge Base
    └── knowledge_base/       # 20 Modular Technical Knowledge Base Documents
```

---

# Module 16: Master Mermaid Architecture Diagrams

## System Architecture & Data Flow Mermaid Diagrams

### 1. High-Level System Architecture

```mermaid
flowchart TD
    CLIENT[React 18 SPA Command Center] -->|HTTP REST + OAuth2 JWT| API[FastAPI Application Gateway]
    API -->|Authenticate & Scope| RBAC[Server-Side Scoping Engine]
    RBAC -->|SQL Queries| DB[(Supabase PostgreSQL 17.6)]
    DB -->|Master Works & Results| API
    API -->|JSON Data & Dossiers| CLIENT
    
    SCRAPER[Live Scraper Spider] -->|SHA-256 Hash Diff| DB
    SCRAPER -->|Raw Records| PIPE[Data Normalization Pipeline]
    PIPE -->|Canonical Parquet| ML[4 Analytical Models Core]
    ML -->|Model Scores & Severities| DB
```

### 2. Database ER Diagram

```mermaid
erDiagram
    works ||--o| cost_anomaly_results : "has cost assessment"
    works ||--o| fund_expenditure_results : "has fund assessment"
    works ||--o| delay_results : "has delay assessment"
    works ||--o{ work_expenditures : "contains payment vouchers"
    works ||--o{ duplicate_work_results : "involved in candidate pair"
    users ||--o{ works : "scopes jurisdiction"
```

---

# Module 17: Viva Questions & Expert Answers

## Technical Viva Questions & Detailed Answers

### Q1: Why did you split anomaly detection into 4 separate models instead of calculating a single composite risk score?
- **Short Answer**: To preserve signal fidelity. Cost overruns, duplicate billing, dormant funds, and statutory delays are fundamentally different risk dimensions.
- **Detailed Answer**: A composite score averages distinct signals. An urgently completed hospital could have zero delay and valid vouchers but an inflated cost estimate. Averaging these scores would mask the cost anomaly. Keeping models independent gives vigilance officers precise, actionable diagnostic reasons for each domain.
- **If Examiner Asks "Why?"**: Composite scores create false negatives by diluting extreme single-dimension anomalies.

---

### Q2: How does Model 1 guarantee zero data leakage?
- **Short Answer**: It evaluates works strictly using features available at sanction time.
- **Detailed Answer**: Model 1 uses only `sanction_amount`, `work_type`, and `state`. It strictly excludes post-sanction features like completion dates, voucher counts, or disbursement amounts.

---

### Q3: How do you prevent Username Enumeration and Timing Attacks on the Login endpoint?
- **Short Answer**: By executing a constant-time dummy bcrypt hash calculation when an email is not found.
- **Detailed Answer**: Standard backends return immediately if an email doesn't exist (~2ms), but execute bcrypt (~90ms) if the email exists. Attackers measure this time difference to harvest valid emails. We execute `DUMMY_BCRYPT_HASH` when an email is missing, forcing every request to take ~90ms regardless of validity.

---

### Q4: Why is District Officer scoping based on `(state, district)` tuples rather than district names alone?
- **Short Answer**: Because district names in India are not unique across states.
- **Detailed Answer**: Exactly 75 district names exist in multiple states (e.g. Bilaspur in Chhattisgarh and Himachal Pradesh). Scoping by district name alone would leak data across state boundaries. We enforce composite tuple scoping: `(assigned_state, assigned_district)`.

---

# Module 18: Technology Selection Justifications

## Technology Selection Justification Matrix

| Technology Selected | Alternative Considered | Why We Chose Selected | Why Alternative Was Rejected |
|---|---|---|---|
| **FastAPI** | Django / Flask | High performance async ASGI, automatic OpenAPI docs, strict Pydantic schema validation. | Django is overly heavy for REST API; Flask lacks native async and Pydantic integration. |
| **Supabase PostgreSQL** | MongoDB | Strict relational schema, foreign key constraints (0 orphan enforcement), native SQL joins. | MongoDB lacks ACID joins needed across works and expenditure tables. |
| **Isolation Forest** | Random Forest / XGBoost | Unsupervised anomaly detection; does not require historical labeled fraud data. | Supervised models require labeled fraud datasets which do not exist in government dumps. |
| **Sentence-BERT (`all-MiniLM-L6-v2`)** | TF-IDF / Cosine | Captures semantic context in work descriptions (e.g. *Water Tank* vs *Storage Reservoir*). | TF-IDF relies on exact word matches and misses semantic duplicates. |
| **Rule Engine (Delay)** | Machine Learning | Statutory SLAs (75d / 365d) are codified legal rules requiring 100% deterministic evaluation. | ML adds unnecessary probability/uncertainty to codified legal timelines. |
| **Bcrypt (12 rounds)** | Plain SHA-256 | Slow password hashing resistant to GPU brute-force attacks. | SHA-256 is too fast, enabling fast offline dictionary attacks. |

---

# Module 19: Hackathon & Evaluator Q&A

## Evaluator & Hackathon Judge Q&A

### Q1: What makes this project innovative compared to a standard government dashboard?
> *"Traditional dashboards only display static totals. The MPLADS AI Command Center actively detects risk: it benchmarks cost estimates against peer medians, matches duplicate work candidates using semantic NLP, flags voucher concentration anomalies, and enforces statutory legal deadlines with automated explainability."*

### Q2: How does the system handle false positives in Duplicate Work Detection?
> *"In municipal governance, legitimate phased works (e.g. Road Phase 1 and Road Phase 2) share similar language. Our duplicate matcher flags candidate pairs for human review rather than automatically deleting records. Vigilance officers receive ranked audit queues with detailed explanation vectors."*

### Q3: How scalable is the architecture?
> *"The backend is stateless and horizontally scalable via FastAPI/Uvicorn. PostgreSQL queries are optimized with composite B-Tree indexes. Dense embeddings are pre-cached, and candidate blocking windows reduce duplicate comparisons by 99.95%."*

---

# Module 20: Final One-Page Reference Cheat Sheet

## One-Page Project Master Reference

- **Project Name**: MPLADS AI Command Center (Governance & Analytics Platform)
- **Core Scope**: 190,942 Master Works | 109,311 Expenditure Vouchers | ₹10,211.49 Cr Sanctioned | 773 Districts | 36 States
- **Stack**: React 18 SPA + Vite + Tailwind | FastAPI + Async Uvicorn | Supabase PostgreSQL 17.6 | PyArrow & Apache Parquet
- **4 Models**:
  1. Cost Anomaly: Hierarchical Peer Isolation Forest (`n_estimators=100`, Sigmoid calibrated)
  2. Duplicate Work: `all-MiniLM-L6-v2` dense embeddings + Structural proximity + 90d Candidate Blocking
  3. Fund Anomaly: Active spend Isolation Forest + HHI concentration + Status Mismatch rules
  4. Delay SLA: Rule Engine enforcing 75-day sanction & 365-day completion SLAs against `2026-09-05`
- **Security**: OAuth2 JWT (`HS256`), Bcrypt 12 rounds, `DUMMY_BCRYPT_HASH` timing attack defense, 4 RBAC Tiers (`MINISTRY`, `STATE_OFFICER`, `DISTRICT_OFFICER`, `MP`), Composite District Scoping `(state, district)`.
- **Validation**: 117/117 Automated Tests Passing (100% Pass Rate). 0 Critical Vulnerabilities.
"""

master_file.write_text(full_text, encoding="utf-8")
docs_master_file.write_text(full_text, encoding="utf-8")

print(f"Master file updated: {master_file} ({master_file.stat().st_size} bytes)")
