# Phase 4.1 — Model 1: Anomalous Cost Estimate Detector Report
**Model Name**: Model 1 (Anomalous Cost Estimate Detector)  
**Model Version**: `cost_anomaly_v1`  
**Status**: `MODEL 1 COMPLETE`  

---

## 1. Executive Summary
Model 1 evaluates the reasonableness of sanctioned/estimated costs for MPLADS works using an unsupervised, hierarchical peer-grouped **Isolation Forest** model. It operates strictly at sanction time with **zero post-sanction leakage**.

## 2. Dataset & Zero-Leakage Verification
- **Input File**: `data/features/cost/cost_anomaly_features.parquet`
- **Total Sanctioned Works Analyzed**: 98,825 rows
- **Zero-Leakage Assertion**: `PASSED` (0 post-sanction columns used)

## 3. Hierarchical Peer Grouping & Fallback Breakdown
Works are grouped hierarchically to compare costs against natural peer groups (e.g. Street Lights vs Roads):
| Peer Group Level | Description | Work Count | Share % |
|---|---|---|---|
| `STATE_WORK_TYPE` | State Work Type | 94,249 | 95.37% |
| `NATIONAL_WORK_TYPE` | National Work Type | 4,466 | 4.52% |
| `NATIONAL_OVERALL` | National Overall | 110 | 0.11% |


## 4. Anomaly Severity Distribution
Scores are normalized into a calibrated `[0.0, 1.0]` interval using sigmoid mapping centered at decision boundary 0.0:
| Severity | Score Range / Rule | Count | Share % | Action / Framing |
|---|---|---|---|---|
| `HIGH` | $\ge 0.75$ | 996 | 1.01% | High priority review |
| `MEDIUM` | $0.50 \le \text{score} < 0.75$ | 4,284 | 4.33% | Standard audit |
| `LOW` | $< 0.50$ | 93,542 | 94.65% | Normal cost estimate |
| `DATA_QUALITY_EXCEPTION` | $< ₹1,000$ sanction amount | 3 | 0.00% | Data entry correction flag |


## 5. Top 10 High Cost-Anomaly Sample Review
| Work ID | State | Work Type | Sanction Amount | Peer Median | Relative Deviation | Score | Severity |
|---|---|---|---|---|---|---|---|
| `WS/MP107/2024-2025/141292` | Madhya Pradesh | `Purchase Books for Library` | ₹2,000,000.00 | ₹100,000.00 | **+1900.0%** | `0.96` | `HIGH` |
| `WS/MP585/2025-2026/178906` | Gujarat | `Crematoriums/energy efficient ` | ₹9,424,000.00 | ₹400,000.00 | **+2256.0%** | `0.95` | `HIGH` |
| `WS/MP18066/2025-2026/169574` | Haryana | `Improvement of electricity dis` | ₹3,000,000.00 | ₹174,000.00 | **+1624.1%** | `0.95` | `HIGH` |
| `WS/MP203/2025-2026/217604` | Uttar Pradesh | `Installation of multi-gym equi` | ₹12,640,000.00 | ₹798,100.00 | **+1483.8%** | `0.94` | `HIGH` |
| `WS/MP18063/2025-2026/246454` | Haryana | `Construction of roads, link ro` | ₹9,386,764.00 | ₹497,000.00 | **+1788.7%** | `0.94` | `HIGH` |
| `WS/MP203/2024-2025/162204` | Uttar Pradesh | `Installation of multi-gym equi` | ₹11,838,120.00 | ₹798,100.00 | **+1383.3%** | `0.94` | `HIGH` |
| `WS/MP758/2026-2027/298110` | Tamil Nadu | `Purchase of smart boards, visu` | ₹2,500,000.00 | ₹200,000.00 | **+1150.0%** | `0.94` | `HIGH` |
| `WS/MP18053/2025-2026/180157` | Gujarat | `Construction of rainwater harv` | ₹4,999,918.00 | ₹175,000.00 | **+2757.1%** | `0.94` | `HIGH` |
| `WS/MP18334/2024-2025/134420` | Andhra Pradesh | `Installing community drinking ` | ₹2,416,479.00 | ₹500,000.00 | **+383.3%** | `0.94` | `HIGH` |
| `WS/MP141/2025-2026/210474` | Punjab | `Construction of community cent` | ₹12,000,000.00 | ₹484,855.00 | **+2375.0%** | `0.94` | `HIGH` |


## 6. Sample Auditable Explanation
> Work ID: WS/MP107/2024-2025/141292 | Sanction Amount: ₹2,000,000.00 (+1900.0% vs peer median ₹100,000.00) | Peer Group: 'MADHYA PRADESH || Purchase Books for Library' (N=125) | Cost Anomaly Score: 0.96 | Severity: HIGH — REQUIRES REVIEW.

## 7. Model Artifacts & Outputs
- **Scored Output Parquet**: `data/model_outputs/cost_anomaly/cost_anomaly_scores.parquet`
- **Global Model Metadata**: `models/cost_anomaly/global_model_metadata.json`
- **Trained Peer Models**: `models/cost_anomaly/peer_models/*.joblib`
