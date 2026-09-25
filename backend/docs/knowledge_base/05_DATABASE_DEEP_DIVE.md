# 05. Database Architecture & ER Deep Dive

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

