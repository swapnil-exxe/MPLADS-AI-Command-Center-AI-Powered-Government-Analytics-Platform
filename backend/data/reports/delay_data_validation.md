# Phase 5: Delay & SLA Logic — Data Validation Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Phase**: Phase 5 — Delay Logic + Severity Logging  
**Date**: 2026-09-08  
**Status**: DATA VALIDATION COMPLETE  

---

## 1. Available Lifecycle Fields

We audited all raw and processed tables (works_sanctioned, works_recommended, works_completed, xpenditures, and canonical_works). The following table documents exact data availability:

| Lifecycle Milestone | Field Name(s) | Table Source | Available Count | Missing Count (Share %) | Data Quality Notes |
|---|---|---|---|---|---|
| **Recommendation Date** | 
ecommended_date | works_recommended, canonical_works | 98,825 | 0 (0.00%) | Valid date strings, range: 2023-06-14 to 2026-09-03 |
| **Sanction Date** | sanction_date | works_sanctioned, canonical_works | 98,825 | 0 (0.00%) | Valid date strings, range: 2023-07-07 to 2026-09-05 |
| **Completion Date** | completion_date | works_completed, canonical_works | 44,417 | 54,408 (55.05%) | Available only for completed works. Range: 2023-08-02 to 2026-09-06 |
| **First Expenditure Date** | xpenditure_date | xpenditures | 71,928 | 26,897 (27.22%) | Present only for works with disbursed payments |
| **Work Status** | work_status | works_sanctioned, canonical_works | 98,825 | 0 (0.00%) | 6 categorical stages (Physical Inspection, Sanction, Vendor ID, etc.) |
| **Rejection Date** | *None* | *None* | 0 | 98,825 (100.0%) | **FIELD DOES NOT EXIST** in raw or processed portal data |
| **Rejection Notification Date**| *None* | *None* | 0 | 98,825 (100.0%) | **FIELD DOES NOT EXIST** in raw or processed portal data |
| **Vendor ID Milestone Date** | *None* | *None* | 0 | 98,825 (100.0%) | Only categorical status exists, no timestamp |
| **Physical Progress %** | *None* | *None* | 0 | 98,825 (100.0%) | Numerical progress percentage does not exist |

---

## 2. Observable vs Non-Observable Delays

| Lifecycle Delay Candidate | Status | Reason & Evidence |
|---|---|---|
| **A. Recommendation → Sanction Delay** | **OBSERVABLE** | Complete timestamps exist for all 98,825 works. Zero negative values. Evaluated against official 75-day SLA. |
| **B. Sanction → Completion Delay** | **PARTIALLY OBSERVABLE** | Complete for all completed works ( = 44,417$). Naturally absent for open/incomplete works ( = 54,408$). Evaluated against 365-day guideline. |
| **C. Open Work Aging** | **OBSERVABLE** | Evaluated for all open/incomplete works ( = 54,408$) against fixed reference date (\text{-}09\text{-}05$). |
| **D. Sanction → First Disbursement** | **PARTIALLY OBSERVABLE** | Observable for active financial cohort ( = 71,928$). (Logged as secondary evidence to avoid modular overlap with Model 3). |
| **E. Vendor Identification Delay** | **NOT OBSERVABLE** | No date field exists for when vendor identification began or ended. |
| **F. Rejection / Notification Delay** | **NOT OBSERVABLE** | No rejection records, rejection timestamps, or notification logs exist in portal data. **No 45-day rejection rule will be manufactured.** |

---

## 3. Official SLA & Guideline Evidence

* **Recommendation to Sanction SLA (75 Days)**:
  * **Source**: Official MPLADS Guidelines (Chapter 3, Para 3.12). The District Authority is mandated to accord sanction within 75 days of receiving the recommendation from the MP.
  * **Data Distribution**:
    * Mean: 106.6 days, Median: 77.0 days
    * 50,432 works (51.03%) exceed 75 days.
    * Because over 50% exceed 75 days, multi-tiered severity scaling is mathematically necessary to distinguish minor procedural lag from severe delay.
* **Work Completion Time Limit (365 Days / 1 Year)**:
  * **Source**: Official MPLADS Guidelines. Normal civil works should be completed within 1 year from the date of administrative/financial sanction.
  * **Data Distribution (Completed Works,  = 44,417$)**:
    * Mean: 182.4 days, Median: 154.0 days
    * 5,370 completed works (12.09%) exceeded 365 days.
  * **Data Distribution (Open Works Aging,  = 54,408$)**:
    * Mean: 245.7 days, Median: 217.0 days
    * 13,768 open works (25.31%) have exceeded 365 days without completion.

---

## 4. Lifecycle Date Distributions (Empirical Analysis)

| Metric | Recommendation → Sanction (=98,825$) | Sanction → Completion (=44,417$) | Open Work Aging (=54,408$) | Sanction → First Disbursement (=71,928$) |
|---|---|---|---|---|
| **Count** | 98,825 | 44,417 | 54,408 | 71,928 |
| **Missing %** | 0.00% | 0.00% | 0.00% | 0.00% |
| **Negative Values** | 0 | 0 | 0 | 0 |
| **Zero Days (Same Day)**| 203 (0.21%) | 1,152 (2.59%) | 0 (0.00%) | 3,263 (4.54%) |
| **p0 (Min)** | 0.0 days | 0.0 days | 0.0 days | 0.0 days |
| **p5** | 12.0 days | 2.0 days | 15.0 days | 1.0 days |
| **p25** | 38.0 days | 72.0 days | 79.0 days | 17.0 days |
| **p50 (Median)** | **77.0 days** | **154.0 days** | **217.0 days** | **72.0 days** |
| **p75** | 140.0 days | 265.0 days | 368.0 days | 162.0 days |
| **p90** | 236.0 days | 385.0 days | 491.0 days | 255.0 days |
| **p95** | 316.0 days | 442.0 days | 583.0 days | 316.0 days |
| **p99** | 461.0 days | 634.0 days | 728.0 days | 450.0 days |
| **p100 (Max)** | 1,100.0 days | 948.0 days | 1,121.0 days | 900.0 days |
| **Mean** | 106.6 days | 182.4 days | 245.7 days | 104.4 days |

---

## 5. Selected vs Rejected Rules

### Selected Rules:
1. **RECOMMENDATION_SANCTION_DELAY**: Evaluates sanction timeliness against the official 75-day SLA for all 98,825 works.
2. **COMPLETION_DELAY**: Evaluates execution timeliness against the 365-day guideline for all completed works ( = 44,417$).
3. **OPEN_WORK_AGING**: Evaluates elapsed duration against the 365-day guideline for all open/incomplete works ( = 54,408$).

### Rejected Rules:
1. **REJECTION_NOTIFICATION_DELAY**: **REJECTED**. Zero rejection records exist in the portal. Implementing an unobservable rule would be fabricated.
2. **VENDOR_IDENTIFICATION_DELAY**: **REJECTED**. Milestone timestamps do not exist.
3. **PHYSICAL_PROGRESS_RATE**: **REJECTED**. No numerical progress percentage exists in source data.
