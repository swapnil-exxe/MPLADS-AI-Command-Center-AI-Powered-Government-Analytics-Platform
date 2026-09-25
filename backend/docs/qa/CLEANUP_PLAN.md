# EXTREME CLEANUP PLAN & DEPENDENCY ANALYSIS — MPLADS PLATFORM

**Date**: September 13, 2026  
**Target Environment**: `/Users/swapnil/Documents/PS102`  
**Initial Workspace Size**: **1.94 GB** (1,989.98 MB, 1,767 files)  

---

## 1. CATEGORIZATION OF DELETION TARGETS

| Target Path / File Pattern | Category | Estimated Size | Dependency Analysis & Safety Justification | Safe to Delete? |
| :--- | :--- | :--- | :--- | :--- |
| `Video/` (Root Directory) | Unused Raw Assets | 218.25 MB | Contains 5 raw uncompressed `.mp4` recordings (`VID_20260909_*.mp4`, `inside.mp4`, `mplads-landing-bg.mp4`). Landing video is served from `frontend/public/videos/mplads-landing-bg.mp4` and `frontend/dist/videos/mplads-landing-bg.mp4`. Root `Video/` is completely unreferenced by API, frontend, or tests. | **YES** |
| `models/` (Root Directory) | Obsolete Prototypes | 102.50 MB | Contains legacy `embeddings_cache.npz` (95.59 MB) and `.joblib` cost anomaly files from early prototypes. Current live system uses `data/model_outputs/` parquet files and SQLite database. Zero imports in `api/`, `ml_models/`, or `database/`. | **YES** |
| `ml/models/` (Root Directory) | Obsolete Prototypes | 150.20 MB | Contains 200+ legacy `.joblib` peer group models from prototype phase. Not loaded anywhere in production `api/` or `ml_models/`. | **YES** |
| `ppt_screenshots/` & `landing_preview.png` | Unused Assets | 1.64 MB | Contains 10 presentation screenshot PNGs unreferenced by code. | **YES** |
| `__pycache__/` (All instances) | Temporary Cache | ~15.00 MB | Python bytecode cache generated automatically at runtime. Safe to purge. | **YES** |
| `.pytest_cache/` (All instances) | Test Cache | ~2.50 MB | Pytest execution state cache. Regenerated automatically on next test run. | **YES** |
| `.DS_Store` (All instances) | OS Metadata | ~0.05 MB | macOS Finder metadata files. Completely unreferenced. | **YES** |
| Temporary Audit Scripts in `scripts/` | Intermediate Utility | ~0.35 MB | `generate_full_audit_matrices.py`, `generate_qa_artifacts.py`, `run_destructive_qa_audit.py`, `generate_recalculation_audit_report.py`, `independent_audit_validation.py`. (Core scripts `verify_full_pipeline.py`, `run_full_ml_pipeline.py`, `security_audit.py` are strictly retained). | **YES** |

---

## 2. PROTECTED CRITICAL FILES (NEVER DELETED)

- **Frontend**: `package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `src/`, `public/`, `dist/` (Required for serving React SPA bundle).
- **Backend API**: `api/main.py`, `api/config.py`, `api/dependencies.py`, `api/auth/`, `api/routers/`, `api/schemas/`.
- **Database**: `database/mplads_master.db` (190,942 works master DB), `database/models.py`, `database/connection.py`, `database/schema.sql`, `database/populate_sqlite.py`, `database/seed_users.py`.
- **ML / Rule Engines**: `ml_models/`, `rule_engines/`, `data/features/shared/canonical_works.parquet`, `data/model_outputs/`.
- **Scraper**: `scraper/spider.py`, `scraper/discovery.py`, `scraper/config.py`, `scraper/models.py`.
- **Tests**: All automated tests in `tests/`.
- **Verification Scripts**: `scripts/verify_full_pipeline.py`, `scripts/run_full_ml_pipeline.py`, `scripts/security_audit.py`.
- **Canonical Documentation**: `README.md`, `EXTREME_QA_FINAL_REPORT.md`, `EXTREME_QA_BUGS.md`, `.gitignore`, `.env`.

---

## 3. ESTIMATED SAVINGS & REDUCTION
- **Initial Workspace Size**: 1,989.98 MB (1.94 GB)
- **Estimated Storage Saved**: **~758 MB** (~0.74 GB)
- **Expected Size After Cleanup**: **~1,231 MB** (~1.20 GB)
- **Percentage Storage Reduction**: **~38.1%**
