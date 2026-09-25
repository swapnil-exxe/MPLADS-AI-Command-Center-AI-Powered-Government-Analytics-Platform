# Phase 5: Delay Logic & SLA Rule Engine Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Phase**: Phase 5 — Delay Logic + Severity Logging  
**Date**: 2026-09-15  
**Status**: `PHASE 5 COMPLETE`  

---

## 1. Executive Summary
Phase 5 implements the deterministic Delay & SLA Rule Engine for all 98,825 active MPLADS works. Grounded in official MPLADS guidelines (Para 3.12 75-day sanction SLA and 365-day completion guideline limit), the engine evaluates observable lifecycle milestones, assigns standardized severities (`NONE`, `LOW`, `MEDIUM`, `HIGH`), and produces a fully explainable, normalized delay score in [0.0, 1.0].

## 2. Dataset & Reference Date Strategy
* **Total Works Analyzed**: 190,942
* **Completed Works Analyzed**: 137,792 (45.0%)
* **Incomplete / Open Works Analyzed**: 53,150 (55.0%)
* **Fixed Reference Date**: `2026-09-05` (latest sanction date in dataset, ensuring complete determinism and reproducibility)
* **Execution Runtime**: 9.63 seconds

## 3. Severity Distribution
| Severity Tier | Work Count | Share % | Definition / Operational Meaning |
|---|---|---|---|
| `NONE` | 63,497 | 33.25% | Fully compliant with 75-day sanction SLA and 365-day execution guideline |
| `LOW` | 32,752 | 17.15% | Minor administrative delay (76–150 days on recommendation -> sanction) |
| `MEDIUM` | 37,624 | 19.7% | Significant delay: 151–225 days on sanction OR 1.0–1.5 years on project execution |
| `HIGH` | 57,069 | 29.89% | Severe delay: >225 days on sanction (>3x SLA) OR >1.5 years on project execution |

## 4. Milestone-Specific Breakdown
* **Recommendation → Sanction SLA (75 Days)**:
  * Exceeded: **98,997** works (51.85%)
  * Within SLA: **91,945** works
* **Sanction → Completion (Completed Works, $N = 137,792$)**:
  * Exceeded 365-day guideline: **32,037** works (23.25%)
  * Completed within 1 year: **105,755** works
* **Open Work Aging (Incomplete Works, $N = 53,150$)**:
  * Exceeded 365-day guideline: **21,506** works (40.46%)
  * Within 1 year allowable window: **31,644** works

## 5. Score Percentiles (Normalized Delay Score [0.0, 1.0])
* **p0 (Min)**: 0.0
* **p25**: 0.1067
* **p50 (Median)**: 0.4167
* **p75**: 0.7333
* **p90**: 1.0
* **p95**: 1.0
* **p99**: 1.0
* **p100 (Max)**: 1.0

## 6. Sample Top Delayed Works
| Work ID | State | Status | Rec->Sanc Days | Sanc->Comp Days | Open Aging Days | Delay Score | Severity |
|---|---|---|---|---|---|---|---|
| `WS/MP588/2025-2026/130496-Crematoriums/energy efficient crematoriums or structures on burial/cremation ground` | Gujarat | Physical Inspection | 527d | 112d | N/A | `1.00` | `HIGH` |
| `WS/MP854/2024-2025/128391-Lighting of public spaces` | Kerala | Physical Inspection | 368d | 169d | N/A | `1.00` | `HIGH` |
| `WS/MP354/2024-2025/128380-Lighting of public spaces` | Kerala | Physical Inspection | 310d | 201d | N/A | `1.00` | `HIGH` |
| `WS/MP460/2024-2025/81573-Street lights` | Telangana | Physical Inspection | 363d | 33d | N/A | `1.00` | `HIGH` |
| `WS/MP354/2024-2025/128382-Lighting of public spaces` | Kerala | Physical Inspection | 310d | 201d | N/A | `1.00` | `HIGH` |
| `WS/MP854/2024-2025/128383-Lighting of public spaces` | Kerala | Physical Inspection | 368d | 212d | N/A | `1.00` | `HIGH` |
| `WS/MP354/2024-2025/128387-Lighting of public spaces` | Kerala | Physical Inspection | 310d | 201d | N/A | `1.00` | `HIGH` |
| `WS/MP460/2024-2025/81571-Street lights` | Telangana | Physical Inspection | 363d | 33d | N/A | `1.00` | `HIGH` |
| `WS/MP482/2025-2026/128388-Construction of public irrigation facilities` | West Bengal | Physical Inspection | 481d | 422d | N/A | `1.00` | `HIGH` |
| `WS/MP460/2024-2025/81568-Street lights` | Telangana | Physical Inspection | 363d | 31d | N/A | `1.00` | `HIGH` |

## 7. Artifacts & Outputs
* **Scored Dataset**: `data/model_outputs/delay_rules/delay_scores.parquet`
* **Report Document**: `data/reports/delay_rule_engine_report.md`
