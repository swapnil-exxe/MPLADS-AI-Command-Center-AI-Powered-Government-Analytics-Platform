# MPLADS ANALYTICS & GOVERNANCE PLATFORM — PROJECT STRUCTURE

```
MPLADS/
│
├── api/                             # FastAPI Backend Service & Routers
│   ├── auth/                        # JWT Security, Password Hashing & RBAC Dependencies
│   ├── routers/                     # Endpoint Routers (Works, Cost, Duplicates, Funds, Delays, Trends, Chat, Admin)
│   ├── schemas/                     # Pydantic Input/Output Validation Models
│   ├── config.py                    # Environment Configuration & Settings
│   ├── dependencies.py              # Database Session & Pagination Dependencies
│   └── main.py                      # FastAPI App Initialization & Single-File SPA Server
│
├── database/                        # Database Storage & Schema Management
│   ├── mplads_master.db             # Master SQLite Local Database (190,942 canonical works)
│   ├── models.py                    # SQLAlchemy Relational ORM Models
│   ├── connection.py                # Database Engine & Session Provider
│   ├── schema.sql                   # Universal PostgreSQL/SQLite DDL Schema
│   ├── populate_sqlite.py           # Bulk Parquet-to-SQLite DB Ingestion Pipeline
│   └── seed_users.py                # Stakeholder Demo User Account Seeder
│
├── ml_models/                       # Machine Learning Analytical Models
│   ├── cost_anomaly/                # Model 1 — IsolationForest Cost Anomaly Detector
│   ├── duplicate_work/              # Model 2 — Jaccard/Similarity Duplicate Work Scorer
│   └── fund_expenditure_anomaly/    # Model 3 — Expenditure Discrepancy & Utilization Scorer
│
├── rule_engines/                    # Statutory Policy Rule Engines
│   └── delay/                       # Model 4 — Statutory Delay SLA Engine (45d / 75d / 180d thresholds)
│
├── scraper/                         # Live Scrapling Web Ingestion Crawler
│   ├── spider.py                    # Scrapling Pipeline Orchestration & Ingestion Logger
│   ├── discovery.py                 # Target Endpoint Discovery & Harvest Engine
│   ├── config.py                    # Scraper Target Settings
│   └── models.py                    # Scraper Output Data Classes
│
├── data/                            # Production Canonical Data Layer
│   ├── features/shared/             # Master Canonical Parquet Dataset (`canonical_works.parquet`, 190,942 rows)
│   └── model_outputs/               # ML & Rule Engine Output Parquets (`cost_anomaly`, `duplicate_work`, `fund`, `delay`)
│
├── dataset/                         # Raw Source Data Layer
│   └── *.csv                        # 24 Raw MoSPI Governance CSV Datasets (863,032 raw rows)
│
├── frontend/                        # Production React SPA & Component Architecture
│   ├── src/                         # React TypeScript Source Code
│   │   ├── components/              # Reusable UI Components (Header, Sidebar, DataTable, MetricCard, Chatbot)
│   │   ├── pages/                   # 14 Frontend Views (LandingPage, Login, Dashboard, Analytics, Summaries, Admin)
│   │   ├── context/                 # AuthContext & Session State Management
│   │   └── App.tsx                  # React Router Navigation & Scoped Guards
│   ├── dist/                        # Production Single-File Bundle (`index.html`, 1,003 kB)
│   ├── public/                      # Static Assets (Logos, Icons, Video)
│   ├── package.json                 # Frontend Dependencies & Build Scripts
│   └── vite.config.ts               # Single-File Vite Bundler Configuration
│
├── tests/                           # Automated Test Suite (117 Tests)
│   ├── test_api.py                  # API Route & Endpoint Integration Tests
│   ├── test_auth_rbac.py            # Auth, JWT, and Jurisdictional RBAC Scoping Tests
│   ├── test_database_ingestion.py   # Database Schema & Table Verification Tests
│   ├── test_delay_rules.py          # Statutory Delay SLA Rule Calculation Tests
│   ├── test_model1_cost_anomaly.py  # IsolationForest Cost Anomaly Tests
│   ├── test_scraper.py              # Scrapling Crawler Reachability & Change Detection Tests
│   ├── test_subho_chatbot.py        # AI Chatbot Security & Prompt Injection Tests
│   └── ...                          # Pipeline & Rollup Verification Tests
│
├── scripts/                         # Maintenance & Verification Pipeline Scripts
│   ├── verify_full_pipeline.py      # End-to-End Pipeline & DB Reconciliation Script
│   ├── run_full_ml_pipeline.py      # Full 4 ML Models Recalculation Engine
│   └── security_audit.py            # Codebase Secret Scanner & Security Audit Tool
│
├── docs/                            # Structured Documentation & Reports
│   ├── architecture/                # System Specs, SRS, & UI Architecture Plans
│   ├── qa/                          # QA Final Reports, Test Matrices, & Bug Logs
│   ├── security/                    # Security Audit & Vulnerability Assessment Reports
│   └── reports/                     # Data Reconciliation Reports & API Collections
│
├── README.md                        # Primary Repository Overview & Quickstart Guide
├── requirements.txt                 # Backend Python Dependencies
└── .env                             # Environment Variables Configuration (Gitignored)
```
