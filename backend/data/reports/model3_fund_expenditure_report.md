# Model 3: Fund & Expenditure Anomaly Detector Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Phase**: Phase 4.3 — Model 3 (Fund & Expenditure Anomaly)  
**Date**: 2026-09-15  
**Status**: `MODEL 3 COMPLETE`  

---

## 1. Executive Summary
Model 3 evaluates the financial flow and expenditure patterns of MPLADS works to detect anomalous fund utilization, unusual tranche fragmentation, disbursement timing latencies, and administrative status-expenditure mismatches.

## 2. Dataset & Cohort Segmentation
* **Total Works Analyzed**: 98,825
* **Active Financial Cohort (Disbursed > 0)**: 71,928 (72.8%)
* **Zero-Disbursement Cohort**: 26,897 (27.2%)
* **Execution Runtime**: 5.09 seconds

## 3. Severity Distribution
| Severity Tier | Work Count | Share % | Definition / Administrative Action |
|---|---|---|---|
| `LOW` | 92,469 | 93.57% | Normal expenditure flow / newly sanctioned awaiting release |
| `MEDIUM` | 5,023 | 5.08% | Watchlist: Elevated anomaly score or dormant sanction (>365 days) |
| `HIGH` | 1,333 | 1.35% | High Priority: Top multi-variate outlier or status-expenditure mismatch |

## 4. Audit Category Breakdown
| Audit Category | Count | Description |
|---|---|---|
| `ACTIVE_EXPENDITURE` | 71,928 | Evaluated via Isolation Forest on continuous financial features |
| `NORMAL_AWAITING_DISBURSEMENT` | 21,765 | Early stage (Sanction/Vendor ID) <= 365 days old |
| `DORMANT_SANCTION` | 4,198 | Sanctioned > 365 days ago with zero fund disbursement |
| `STATUS_EXPENDITURE_MISMATCH` | 934 | Completed / Physical Inspection with zero expenditure vouchers |

## 5. Active Cohort Calibrated Score Percentiles
* **p0 (Min)**: 0.0062
* **p50 (Median)**: 0.0215
* **p75**: 0.0525
* **p90**: 0.1442
* **p95**: 0.302
* **p97 (Decision Cutoff)**: 0.45
* **p99**: 0.6049
* **p100 (Max)**: 0.9205

## 6. Sample Top Anomalies
| Work ID | State | Status | Sanction Amount | Disbursed Amount | Utilization | Tranches | Score | Severity |
|---|---|---|---|---|---|---|---|---|
| `WS/MP134/2025-2026/239327` | Odisha | Work partially Completed | ₹49,500,000.00 | ₹7,821,253.00 | 15.8% | 14 | `0.92` | `HIGH` |
| `WS/MP719/2025-2026/230890` | Rajasthan | Physical Inspection | ₹499,974.00 | ₹285,163.00 | 57.0% | 25 | `0.91` | `HIGH` |
| `WS/MP843/2025-2026/219625` | Punjab | Work partially Completed | ₹3,000,000.00 | ₹2,163,133.00 | 72.1% | 29 | `0.91` | `HIGH` |
| `WS/MP18328/2025-2026/252741` | Himachal Pradesh | Vendor Identification | ₹1,000,000.00 | ₹335,094.00 | 33.5% | 16 | `0.90` | `HIGH` |
| `WS/MP18162/2025-2026/187436` | Rajasthan | Work Completed | ₹500,000.00 | ₹83,750.00 | 16.8% | 8 | `0.90` | `HIGH` |
| `WS/MP18155/2025-2026/183794` | Punjab | Vendor Identification | ₹500,000.00 | ₹388,927.00 | 77.8% | 13 | `0.90` | `HIGH` |
| `WS/MP140/2024-2025/135348` | Punjab | Vendor Identification | ₹1,100,000.00 | ₹895,347.00 | 81.4% | 22 | `0.89` | `HIGH` |
| `WS/MP18328/2025-2026/252745` | Himachal Pradesh | Vendor Identification | ₹1,000,000.00 | ₹325,285.00 | 32.5% | 20 | `0.89` | `HIGH` |
| `WS/MP140/2024-2025/164182` | Punjab | Work partially Completed | ₹1,600,000.00 | ₹826,634.00 | 51.7% | 23 | `0.89` | `HIGH` |
| `WS/MP18152/2024-2025/158093` | Punjab | Vendor Identification | ₹1,200,000.00 | ₹718,382.00 | 59.9% | 15 | `0.89` | `HIGH` |

## 7. Model Artifacts
* **Scored Output Dataset**: `data/model_outputs/fund_expenditure_anomaly/fund_expenditure_scores.parquet`
* **Trained Model**: `models/fund_expenditure_anomaly/isolation_forest.joblib`
* **Robust Scaler**: `models/fund_expenditure_anomaly/robust_scaler.joblib`
* **Metadata JSON**: `models/fund_expenditure_anomaly/model_metadata.json`
