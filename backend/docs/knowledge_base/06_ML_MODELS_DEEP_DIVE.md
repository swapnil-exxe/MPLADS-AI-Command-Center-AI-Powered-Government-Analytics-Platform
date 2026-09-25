# 06. Analytical & Machine Learning Core Models

## The 4 Independent Analytical Core Models

The platform strictly avoids artificial risk score averaging. Each model evaluates a distinct compliance dimension:

---

### Model 1: Cost Anomaly Detector (`ml_models/cost_anomaly/`)
- **Purpose**: Evaluates cost estimate reasonableness at sanction time.
- **Zero-Leakage**: Uses 0 post-sanction features.
- **Hierarchical Peer Grouping**:
  1. `STATE_WORK_TYPE` (Primary, >95% works)
  2. `NATIONAL_WORK_TYPE` (Fallback for peer count < 15)
  3. `NATIONAL_OVERALL` (Emergency fallback for peer count < 15)
- **Algorithm**: Peer-trained Isolation Forest (`n_estimators=100`, `contamination=0.01`). Raw output mapped to `[0,1]` via calibrated Sigmoid transformation.

---

### Model 2: Duplicate Work Detector (`ml_models/duplicate_work/`)
- **Purpose**: Identifies potential duplicate project sanctions.
- **Candidate Blocking**: 90-day sanction date window within identical state and category (reduces pairwise checks from 4.88B to 2.02M).
- **Embedding Transformer**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Scoring Formula**:
  $$\text{duplicate\_score} = 0.65 \times \text{semantic\_similarity} + 0.35 \times \text{structural\_score}$$
  Where structural score combines amount similarity, date proximity, same MP, and same constituency flags.

---

### Model 3: Fund & Expenditure Anomaly Detector (`ml_models/fund_expenditure_anomaly/`)
- **Purpose**: Monitors payment concentration, velocity, and status mismatches.
- **Cohorts**:
  - Active Spenders (Disbursed > 0): Isolation Forest trained on 6 features including Herfindahl-Hirschman Index (HHI) voucher concentration.
  - Zero-Disbursement (Disbursed = 0): Deterministic rules flagging dormant sanctions (>365d old) and status-expenditure mismatches (marked complete but 0 vouchers).

---

### Phase 5: Delay & Statutory SLA Rule Engine (`rule_engines/delay/`)
- **Purpose**: Enforces statutory timelines mandated by Para 3.12 of MPLADS Guidelines.
- **Track 1**: Recommendation to Sanction SLA (75-Day limit).
- **Track 2**: Sanction to Completion SLA (365-Day limit).
- **Track 3**: Open Work Aging evaluated against reference date `2026-09-05`.

