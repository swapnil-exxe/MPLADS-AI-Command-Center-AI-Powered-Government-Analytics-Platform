# MPLADS 190942 — FULL ORIGINAL DATA RECONCILIATION REPORT

## 1. Authoritative Source Dataset Inventory

| Relative File Path | Corpus / House | Rows | Cols | Date Range | Missing Values | Duplicate Rows |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `LokSabha17/Allocated Limit for Honble MPs_LokSabha_17.csv` | LokSabha17 | 544 | 5 | N/A to N/A | 3 | 0 |
| `LokSabha17/Expenditure on Completed and On-going Works as on Date_LokSabha17.csv` | LokSabha17 | 138,575 | 11 | 2023-07-31 to 2026-09-05 | 0 | 0 |
| `LokSabha17/Works Completed_LokSabha_17.csv` | LokSabha17 | 71,256 | 11 | 2023-07-26 to 2026-09-06 | 21,641 | 0 |
| `LokSabha17/Works Recommended_LokSabha_17.csv` | LokSabha17 | 94,749 | 11 | 2019-05-23 to 2026-09-05 | 3,056 | 0 |
| `LokSabha17/Works Sanctioned_LokSabha_17.csv` | LokSabha17 | 92,117 | 12 | 2019-08-18 to 2026-02-04 | 252 | 0 |
| `LokSabha18/Allocated Limit for Honble MPs_LokSabha_18.csv` | LokSabha18 | 544 | 5 | N/A to N/A | 1 | 0 |
| `LokSabha18/Amount consented for Calamity_LokSabha_18.csv` | LokSabha18 | 13 | 6 | 2024-09-03 to 2025-12-07 | 0 | 0 |
| `LokSabha18/Expenditure on Completed and On-going Works as on Date_LokSabha_18.csv` | LokSabha18 | 84,172 | 11 | 2024-07-25 to 2026-09-06 | 0 | 0 |
| `LokSabha18/Works Completed_LokSabha_18.csv` | LokSabha18 | 34,440 | 11 | 2024-08-12 to 2026-09-06 | 9,462 | 0 |
| `LokSabha18/Works Recommended_LokSabha_18.csv` | LokSabha18 | 107,024 | 11 | 2024-07-08 to 2026-09-05 | 28,287 | 0 |
| `LokSabha18/Works Sanctioned_LokSabha_18.csv` | LokSabha18 | 79,220 | 12 | 2024-07-08 to 2026-09-03 | 98 | 0 |
| `RajyaSabha_Retired/Allocated Limit for Honble MPs (1).csv` | RajyaSabha_Retired | 232 | 5 | N/A to N/A | 0 | 0 |
| `RajyaSabha_Retired/Amount consented for Calamity.csv` | RajyaSabha_Retired | 21 | 6 | 2024-09-10 to 2025-11-17 | 0 | 0 |
| `RajyaSabha_Retired/Expenditure on Completed and On-going Works as on Date.csv` | RajyaSabha_Retired | 25,130 | 11 | 2023-07-27 to 2026-09-05 | 0 | 0 |
| `RajyaSabha_Retired/Works Completed.csv` | RajyaSabha_Retired | 9,964 | 11 | 2023-08-02 to 2026-09-05 | 3,492 | 0 |
| `RajyaSabha_Retired/Works Recommended.csv` | RajyaSabha_Retired | 25,204 | 11 | 2023-06-14 to 2026-09-05 | 5,854 | 0 |
| `RajyaSabha_Retired/Works Sanctioned.csv` | RajyaSabha_Retired | 19,607 | 12 | 2023-06-14 to 2026-09-02 | 18 | 0 |
| `RajyaSabha_Sitting/Allocated_Limit_for_Honble_MPs_Rajya_Sabha.csv` | RajyaSabha_Sitting | 232 | 5 | N/A to N/A | 0 | 0 |
| `RajyaSabha_Sitting/Amount_consented_for_Calamity_Rajya_Sitting.csv` | RajyaSabha_Sitting | 21 | 6 | 2024-09-10 to 2025-11-17 | 0 | 0 |
| `RajyaSabha_Sitting/Expenditure_on_Completed_and_On-going_Works_as_on_Date_Rajya_Sitting.csv` | RajyaSabha_Sitting | 25,141 | 11 | 2023-07-27 to 2026-09-06 | 0 | 0 |
| `RajyaSabha_Sitting/Works_Completed_Rajya_Sitting.csv` | RajyaSabha_Sitting | 9,979 | 11 | 2023-08-02 to 2026-09-06 | 3,492 | 0 |
| `RajyaSabha_Sitting/Works_Recommended_Rajya_Sitting.csv` | RajyaSabha_Sitting | 25,240 | 11 | 2023-06-14 to 2026-09-06 | 5,889 | 0 |
| `RajyaSabha_Sitting/Works_Sanctioned_Rajya_Sitting.csv` | RajyaSabha_Sitting | 19,607 | 12 | 2023-06-14 to 2026-09-02 | 18 | 0 |

- **Total Discovered Files**: 23 CSV datasets
- **Total Processed Raw Records**: 863,032

---

## 2. Canonical Master Dataset Statistics

- **Master Canonical Works**: **98,825** unique work items across all 4 corpora (`LokSabha17`, `LokSabha18`, `RajyaSabha_Retired`, `RajyaSabha_Sitting`)
- **Master Expenditure Vouchers**: **109,311** records
- **Total Disbursed Capital Outlay**: **₹40,220,574,336.14**
- **State Coverage**: **36** States & Union Territories
- **District Coverage**: **861** Districts
- **MP Coverage**: **714** Members of Parliament

---

## 3. Model Outputs & Analytical Pipeline Results

### Model 1: Cost Anomaly Detection (Isolation Forest)
- **Output Parquet**: `data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet`
- **Total Evaluated Works**: 98,825
- **Severity Distribution**:
  - `LOW`: 93,542
  - `MEDIUM`: 4,284
  - `HIGH`: 996
  - `DATA_QUALITY_EXCEPTION`: 3

### Model 2: Potential Duplicate Work Detection (SentenceTransformers + Cosine Similarity)
- **Output Parquets**: `data/model_outputs/duplicate_work/duplicate_scores.parquet` & `duplicate_review.parquet`
- **Candidate Pairs Scored**: 1,803,361 pairs
- **Review Queue Candidates**: 1,329,871 pairs (Top 50,000 ingested into database)

### Model 3: Fund & Expenditure Anomaly Detection
- **Output Parquet**: `data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet`
- **Total Evaluated Works**: 98,825
- **Severity Distribution**:
  - `LOW`: 92,469
  - `MEDIUM`: 5,023
  - `HIGH`: 1,333

### Model 4: Statutory Delays & Trend Rollups
- **Output Parquet**: `data/model_outputs/delay_rules/delay_scores.parquet`
- **Severity Distribution**:
  - `NONE`: 38,233
  - `LOW`: 21,803
  - `MEDIUM`: 23,526
  - `HIGH`: 15,263
- **Quarterly Rollups**: 7,196 rollup rows (`data/model_outputs/trends/trend_quarterly_rollups.parquet`)
- **Active Early Warnings**: 64,161 alerts (`data/model_outputs/trends/early_warnings_active.parquet`)

---

## 4. API & Dashboard Reconciliation Table

| Metric | Dashboard Value | API Endpoint Response | Canonical File Count | Source File Lineage | Status |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **All-India Total Works** | 98,825 | 98,825 | 98,825 | `data/features/shared/canonical_works.parquet` | **MATCH** |
| **National High Cost (M1)** | 996 | 996 | 996 | `data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet` | **MATCH** |
| **National Duplicate Pairs (M2)** | 50,000 | 50,000 | 50,000 | `data/model_outputs/duplicate_work/duplicate_review.parquet` | **MATCH** |
| **National High Fund Flags (M3)** | 1,333 | 1,333 | 1,333 | `data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet` | **MATCH** |
| **National High Delays (M4)** | 15,263 | 15,263 | 15,263 | `data/model_outputs/delay_rules/delay_scores.parquet` | **MATCH** |
| **Uttar Pradesh Works** | 19,912 | 19,912 | 19,912 | `LokSabha17`, `LokSabha18`, `RajyaSabha_*` CSVs | **MATCH** |
| **Uttar Pradesh High Cost** | 275 | 275 | 275 | `cost_anomaly_results` table in DB | **MATCH** |
| **Uttar Pradesh High Fund** | 218 | 218 | 218 | `fund_expenditure_results` table in DB | **MATCH** |
| **Uttar Pradesh High Delays** | 2,200 | 2,200 | 2,200 | `delay_results` table in DB | **MATCH** |
| **PATNA District Works** | 721 | 721 | 721 | `dataset/LokSabha17`, `dataset/LokSabha18` | **MATCH** |
| **PATNA Sanction Outlay** | ₹68.7 Cr | ₹68.7 Cr | ₹68.7 Cr | `works` table aggregation | **MATCH** |
| **PATNA Disbursed Capital** | ₹61.1 Cr | ₹61.1 Cr | ₹61.1 Cr | `work_expenditures` table aggregation | **MATCH** |
| **PATNA High Cost Anomalies** | 1 | 1 | 1 | `cost_anomaly_results` filtered by PATNA | **MATCH** |
| **PATNA High Delays** | 5 | 5 | 5 | `delay_results` filtered by PATNA | **MATCH** |

---

## 5. Affirmations

- **No Synthetic Data**: 100% of data is derived from the 23 raw CSV files in `/Users/swapnil/Documents/PS102/dataset/`.
- **No Hardcoded KPI Numbers**: All dashboard components dynamically render live metrics from API endpoints.
- **NULL Value Integrity**: Missing values are preserved (`NULL ≠ 0`).
- **Strict Data Lineage**: Every number on the dashboard traces back to source data through feature engineering and model pipelines.
