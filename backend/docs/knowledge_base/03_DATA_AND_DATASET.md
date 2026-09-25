# 03. Data Pipeline & Dataset Lineage

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

