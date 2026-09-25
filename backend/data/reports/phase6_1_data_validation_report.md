# Phase 6.1: Database & Data Ingestion Validation Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Database**: PostgreSQL 17.6 on Supabase (`ap-northeast-1`)  
**Phase**: Phase 6.1 — Database Setup & Reliable Data Ingestion  
**Date**: 2026-09-10 13:17:57  
**Status**: `PHASE 6.1 COMPLETE & VERIFIED`  

---

## 1. Relational Table Ingestion Summary

All canonical data, transactional vouchers, and independent model outputs were successfully ingested into Supabase PostgreSQL:

| Table Name | Source Dataset | Rows Ingested | Primary Key | Foreign Key Status |
|---|---|---|---|---|
| `works` | `data/features/shared/canonical_works.parquet` | **98,825** | `work_id` | Master Table (0 duplicates) |
| `cost_anomaly_results` | `data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet` | **98,825** | `work_id` | **100% matched** (0 orphaned) |
| `fund_expenditure_results` | `data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet` | **98,825** | `work_id` | **100% matched** (0 orphaned) |
| `delay_results` | `data/model_outputs/delay_rules/delay_scores.parquet` | **98,825** | `work_id` | **100% matched** (0 orphaned) |
| `work_expenditures` | `data/processed/*/expenditures.parquet` | **109,311** | `id (BIGSERIAL)` | **100% matched** (0 orphaned) |
| `duplicate_work_results`| `data/model_outputs/duplicate_work/duplicate_review.parquet` (Top Flagged) | **50,000** | `id (BIGSERIAL)` | **100% matched** (0 orphaned) |

---

## 2. Integrity & Referential Verification

* **Unmatched / Orphaned Records**:
  * `cost_anomaly_results`: **0** orphaned rows
  * `fund_expenditure_results`: **0** orphaned rows
  * `delay_results`: **0** orphaned rows
  * `duplicate_work_results` (`work_id_1`): **0** orphaned rows
  * `duplicate_work_results` (`work_id_2`): **0** orphaned rows
* **Foreign Key Violations**: **0 (Zero)**
* **Duplicate Primary Keys**: **0 (Zero)**
* **Idempotency**: Rerunning the ingestion script utilizes `ON CONFLICT DO UPDATE` and clean staging tables to guarantee zero record duplication.

---

## 3. Preserved Model Severities in PostgreSQL

Each model output is stored **independently** in its dedicated table without any composite score or cross-model averaging:

### A. Model 1 — Cost Anomaly Results
{
  "LOW": 93542,
  "MEDIUM": 4284,
  "HIGH": 996,
  "DATA_QUALITY_EXCEPTION": 3
}

### B. Model 2 — Duplicate Work Results
{
  "HIGH": 50000
}

### C. Model 3 — Fund & Expenditure Anomaly Results
{
  "LOW": 92469,
  "MEDIUM": 5023,
  "HIGH": 1333
}

### D. Phase 5 — Delay Results
{
  "NONE": 38233,
  "MEDIUM": 23526,
  "LOW": 21803,
  "HIGH": 15263
}

---

## 4. Conclusion & Readiness
The PostgreSQL data layer on Supabase is fully populated and verified. All relational constraints and indexes are established and ready for **Phase 6.2 — FastAPI Backend**.
