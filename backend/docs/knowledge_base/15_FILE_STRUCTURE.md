# 15. Complete Repository File Map

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

