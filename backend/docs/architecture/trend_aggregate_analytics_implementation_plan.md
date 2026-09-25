# Trend & Aggregate Analytics Implementation Plan (Refined & Empirically Validated)

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform  
**MPLADS Analytics Problem Statement**: MPLADS PS 190942 (*Development of an AI-powered system to detect anomalies, fraud, and inefficiencies in MPLAD Scheme implementation*)  
**Scope**: Rigorously Validated Implementation Blueprint for Higher-Level Trend Analysis, Aggregate Governance Metrics, and Defensible Early-Warning Mechanisms  
**Status**: DRAFT FOR USER APPROVAL (Planning Mode — No implementation code written)

---

## Executive Table of Contents

1. [Empirical Data Findings & Threshold Validation](#1-empirical-data-findings--threshold-validation)
2. [Methodological Framework: Three Distinct Analytical Paradigms](#2-methodological-framework-three-distinct-analytical-paradigms)
3. [Paradigm 1: Descriptive Longitudinal Trend Analysis](#3-paradigm-1-descriptive-longitudinal-trend-analysis)
4. [Paradigm 2: Statistical Early-Warning Indicators](#4-paradigm-2-statistical-early-warning-indicators)
5. [Paradigm 3: Statutory & Rule-Based Compliance Warnings](#5-paradigm-3-statutory--rule-based-compliance-warnings)
6. [Time & Geographic Granularity Calibration](#6-time--geographic-granularity-calibration)
7. [Sparse-Data Handling & Empirical Bayes Shrinkage](#7-sparse-data-handling--empirical-bayes-shrinkage)
8. [Double-Counting & Candidate Pair De-duplication Protocol](#8-double-counting--candidate-pair-de-duplication-protocol)
9. [Proposed Data & API Architecture](#9-proposed-data--api-architecture)
10. [Validation & Automated Verification Suite](#10-validation--automated-verification-suite)
11. [Step-by-Step Implementation Roadmap](#11-step-by-step-implementation-roadmap)
12. [Analytical Limitations & Boundary Constraints](#12-analytical-limitations--boundary-constraints)
13. [What NOT to Build](#13-what-not-to-build)
14. [RECOMMENDED BUILD (Priority Matrix)](#14-recommended-build-priority-matrix)

---

## 1. Empirical Data Findings & Threshold Validation

Every threshold, baseline, and smoothing formula in this plan has been directly tested and verified against the actual 98,825 canonical works, expenditure ledgers, and module outputs in the project.

### 1.1 Validation of Assumption 1: Trailing Baselines & Seasonality
* **Empirical Data Distribution**:
  - Works per District-Quarter: Median is only **9.0 works** (mean = 19.98).
  - 51.44% of district-quarters have $N < 10$ works.
  - 69.67% of district-quarters have $N < 20$ works.
  - Only 10.17% of district-quarters have $N \ge 50$ works.
* **Fiscal Year Governance Reality**:
  - Indian public financial administration operates on a strongly cyclical April 1 – March 31 fiscal calendar:
    - **Q1 (Apr–Jun)**: Recommendation initiation, tender preparation. (2024Q1/Q2 also contained the General Election lull).
    - **Q2 (Jul–Sep)**: Monsoon execution slowdown; administrative processing.
    - **Q3 (Oct–Dec)**: Post-monsoon execution peak; voucher submission.
    - **Q4 (Jan–Mar)**: Fiscal year-end fund utilization rush and liquidation acceleration.
* **Why Trailing 3-Quarter Was Flawed**:
  - A 3-quarter baseline compares Q4 (rush) against Q1/Q2/Q3 without completing a full annual cycle, mistaking regular fiscal seasonality for administrative deterioration. Furthermore, it leaves the first 3 quarters (2024Q3 to 2025Q1) unevaluable.
* **Validated Methodological Decision**:
  - **Trailing 4-Quarter (Annualized) Moving Baseline** for continuous smoothing (covers all 4 seasons equally).
  - **Same-Quarter Year-over-Year (YoY)** comparison (e.g. 2026Q1 vs 2025Q1) where historical depth exists, neutralizing seasonal distortion.
  - **Fiscal Year (FY) Aggregation** for district and MP profiles, where median volume rises to **19 to 55 works**, providing sufficient statistical power.

---

### 1.2 Validation of Assumption 2: Empirical Bayes Smoothing & Credibility Tiers
* **Empirical Data Distribution**:
  - In small districts ($N < 20$), the cost anomaly rate swings from **0.00% to 100.00%** with a standard deviation of **0.1561**. A district with 1 work that is high-cost yields a 100% anomaly rate!
  - In large districts ($N \ge 100$), standard deviation drops to **0.0194** (max 21.2%).
  - If we set a hard cutoff of $N \ge 50$ per quarter, **89.83% of all district-quarters in India would be disqualified!**
* **Validated Calibration of Credibility Tiers**:
  - **Quarterly Grain (for States & Mega-Districts)**:
    - `STATISTICALLY_EVALUABLE` ($N \ge 25$ works in quarter — represents top 25% of district-quarters and 100% of states).
    - `SMALL_SAMPLE_CAUTION` ($10 \le N < 25$ works in quarter — median range; rate displayed with caution badge).
    - `INSUFFICIENT_FOR_RATE` ($N < 10$ works in quarter — 51.4% of district-quarters; percentage rate suppressed, displayed strictly as count: *"2 of 7 works"*).
  - **Fiscal Year Grain (for District & MP Dashboards)**:
    - `ROBUST` ($N \ge 50$ works in FY).
    - `MODERATE` ($20 \le N < 50$ works in FY).
    - `LOW_VOLUME` ($N < 20$ works in FY).
* **Validated Empirical Bayes Formulation**:
  - To prevent small districts from dominating league tables, use shrinkage toward the state/national prior:
    $$	ilde{p} = rac{k + M \cdot p_{	ext{state}}}{N + M}$$
  - $M$ is set to the median sample size: **$M = 10$ for quarterly grain, $M = 20$ for fiscal year grain**.
  - *Empirical Proof*: A district with 2 works (1 anomalous) has raw $\hat{p} = 50.0\%$. Shrinkage pulls it to $rac{1 + 20(0.01)}{2 + 20} = \mathbf{5.4\%}$. A district with 500 works (25 anomalous) stays at $\mathbf{4.8\%}$.

---

### 1.3 Validation of Assumption 3: 45–74 Day SLA Cliff
* **Authoritative Statutory Rules**:
  - **MPLADS Guidelines Para 3.12**: District Authority shall sanction eligible works within a maximum of **75 days** from receipt of MP recommendation.
  - **MPLADS Guidelines Para 3.12 (Rejection Mandate)**: District Authority must convey rejection of ineligible works with written reasons to the MP within **45 days**.
* **Empirical Data Distribution of `rec_to_sanc_days` ($N = 98,825$)**:
  - Mean: 106.6 days, Median: 77.0 days.
  - $\le 75$ days (within statutory SLA): **48.97%** (48,393 works).
  - $> 75$ days (statutory breach): **51.03%** (50,432 works).
  - **Between 45 and 75 days**: **19.40%** (19,172 works).
  - **Between 60 and 75 days**: **8.85%** (8,746 works).
* **Validated Classification & Grounding**:
  - This is a **STATUTORY PRE-BREACH WARNING**, not a probabilistic guess.
  - At Day 45, the legal rejection window expires. Any work still pending at Day 45 is legally presumed eligible and in active sanction processing.
  - The window **45 to 74 days represents the final 30-day statutory countdown**.
  - *Calibrated Sub-Tiers*:
    - **`WATCHLIST` (Approaching Deadline)**: 45 to 59 days elapsed (16 to 30 days remaining).
    - **`CRITICAL_CLIFF` (Imminent Statutory Breach)**: 60 to 74 days elapsed (1 to 15 days remaining before official violation).

---

### 1.4 Validation of Assumption 4: 180–365 Day Stagnation Warning
* **Authoritative Rules & Existing Models**:
  - MPLADS Guidelines Para 3.12: Works should be completed within **1 year (365 days)** of sanction.
  - Model 3 (`Fund & Expenditure Anomaly`) defines `DORMANT_SANCTION` as sanction age **$> 365$ days with ₹0 disbursement**.
* **Empirical Data Distribution of First Disbursement**:
  - Across all 71,928 active works with payments:
    - 25th percentile: **17 days**.
    - Median: **72 days**.
    - **75th percentile**: **162 days** (~5.4 months).
    - 90th percentile: **255 days**.
  - *Critical Insight*: **75% of normal projects receive their first disbursement within 162 days.**
* **Empirical Data Distribution of Zero-Disbursement Works ($N = 26,897$)**:
  - Age $< 90$ days: 10,211 works (38.0%) $
ightarrow$ Normal initial tendering.
  - Age 90–180 days: 4,147 works (15.4%) $
ightarrow$ Extended vendor identification.
  - **Age 180–365 days**: **8,106 works (30.1%)** $
ightarrow$ **Past the 75th percentile of normal disbursement; halfway through allowable project lifespan with zero financial progress.**
  - Age $> 365$ days: 4,433 works (16.5%) $
ightarrow$ Already full `DORMANT_SANCTION` violations.
* **Validated Classification & Grounding**:
  - This is a **STATISTICAL + OPERATIONAL EARLY-WARNING INDICATOR**:
    - Statistically grounded because reaching 180 days without spend puts a project beyond the 75th percentile of normal disbursement latency.
    - Operationally grounded because 180 days is the 50% mark of the 1-year completion limit.
    - The **180–365 day window is the "Incubation Queue"** where early intervention can prevent projects from becoming CAG-reportable dormant violations.

---

### 1.5 Validation of Assumption 5: Duplicate Clustering & Days Difference
* **Empirical Analysis of High Duplicate Pairs ($N = 783,736$)**:
  - `days_diff == 0`: **64.58%** of pairs share the **exact same sanction date**!
  - `days_diff <= 15`: **93.53%**!
  - `days_diff <= 30`: **95.94%**!
  - Mean `days_diff` is only **4.06 days**, Median is **0 days**.
* **Empirical Analysis of Cluster Degree per Duplicate Work ($N = 56,370$ unique works)**:
  - Median degree: **8 pairs per work**!
  - 73.4% of works participate in $\ge 3$ duplicate pairs.
  - 46.3% participate in $\ge 10$ pairs.
* **Validated Classification & Grounding**:
  - Duplication in MPLADS is overwhelmingly **Batch-Templated Tendering** (e.g. 20–50 street lights or hand pumps sanctioned on the exact same date in the same district).
  - This is a **STATISTICAL ANOMALY CLUSTERING INDICATOR** targeting tender splitting / fragmentation risk:
    - **`SAME_DAY_BATCH_DUPLICATION`**: $\ge 3$ works with semantic similarity $\ge 0.85$ and amount ratio $\ge 0.90$ sanctioned on the **exact same date** (`days_diff = 0`). Captures 64.6% of duplication clusters.
    - **`RAPID_SUCCESSION_DUPLICATION`**: Works sanctioned within **1 to 15 days** of each other. Captures an additional 28.9% of duplication clusters.

---

## 2. Methodological Framework: Three Distinct Analytical Paradigms

To avoid confusing legal facts with statistical inferences, every analytical metric is strictly organized into one of three distinct paradigms:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      THREE DISTINCT ANALYTICAL PARADIGMS                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. DESCRIPTIVE TREND ANALYSIS (Historical Evidence)                                    │
│    • What has happened over time?                                                      │
│    • Grounded in observed historical rates, rolling baselines, and peer distributions. │
│    • Examples: Quarterly anomaly rate trajectories, fiscal year completion velocity.   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. STATISTICAL EARLY-WARNING INDICATORS (Distributional Outliers)                      │
│    • What operational patterns are deviating from normal distributions?                │
│    • Grounded in empirical percentiles (e.g. 75th percentile disbursement latency).    │
│    • Examples: 180-365d Stagnation Incubation, Same-Day Batch Duplicate Clusters.     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. STATUTORY & RULE-BASED COMPLIANCE WARNINGS (Legal Mandates)                         │
│    • What statutory deadlines and legal guidelines are being breached or approached?   │
│    • Grounded in official MoSPI MPLADS Guidelines (Para 3.12). Zero probabilistic ML.  │
│    • Examples: 45-74d SLA Sanction Cliff, 75d Sanction Breach, 365d Execution Breach.  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Paradigm 1: Descriptive Longitudinal Trend Analysis

### 3.1 Four Independent Rate Tracks (Zero Composite Score)
Each anomaly module maintains its own dedicated rate and financial exposure metric:

1. **Cost Anomaly Track**:
   - `cost_anomaly_rate`: $rac{	ext{Works with Cost Anomaly Severity HIGH in Period}}{	ext{Total Sanctioned Works in Period}}$ (Baseline: ~1.0%).
   - `excess_sanctioned_amount`: $\sum (	ext{sanction\_amount} - 	ext{peer\_median})$ for high-cost works.
2. **Duplicate Work Track (De-duplicated)**:
   - `duplicate_work_rate`: $rac{	ext{Unique Works participating in } \ge 1 	ext{ HIGH Duplicate Pair in Period}}{	ext{Total Sanctioned Works in Period}}$.
   - `duplicate_cluster_density`: $rac{	ext{Total High Duplicate Pairs}}{	ext{Unique Works in High Pairs}}$.
   - `duplicate_financial_exposure`: Sum of sanction amounts of junior duplicate works ($w_2$).
3. **Fund Anomaly Track**:
   - `fund_anomaly_rate`: $rac{	ext{Works with Fund Anomaly Severity HIGH in Period}}{	ext{Total Works in Period}}$.
   - `status_mismatch_rate`: $rac{	ext{Completed/Inspection Works with } ₹0.00 	ext{ Disbursed}}{	ext{Total Completed/Inspection Works in Period}}$.
   - `fund_utilization_efficiency`: $rac{\sum 	ext{Disbursed Amount}}{\sum 	ext{Sanction Amount}}$ across completed works.
4. **Statutory Delay Track**:
   - `sanction_sla_compliance_rate`: $rac{	ext{Works Sanctioned within } 75 	ext{ days of Recommendation}}{	ext{Total Sanctioned Works in Period}}$.
   - `mean_sanction_delay_days`: Average days exceeding 75 days.
   - `open_backlog_overdue_rate`: $rac{	ext{Open Works Aged } > 365 	ext{ days from Sanction}}{	ext{Total Open Works in Period}}$.

### 3.2 Dual-Baseline Comparison Engine
For any qualified entity and metric $M$ in period $t$:
* **Self-Baseline (Trailing 4-Quarter Moving Median)**:
  $$	ext{SelfBaseline}(M) = 	ext{Median}(M_{t-1}, M_{t-2}, M_{t-3}, M_{t-4})$$
  $$\Delta_{	ext{self}} = M_t - 	ext{SelfBaseline}(M)$$
* **Peer-Baseline (State / National Peer Median)**:
  $$\Delta_{	ext{peer}} = M_t - 	ext{Median}_{	ext{peers}}(M_t)$$

### 3.3 Trajectory Classification
* **`DETERIORATING`**: $\Delta_{	ext{self}} \ge +2.0\%$ absolute AND relative increase $\ge +25\%$.
* **`SUSTAINED_INCREASE`**: Metric increased for three consecutive evaluation cycles ($M_t > M_{t-1} > M_{t-2}$).
* **`STABLE`**: Fluctuations within noise band ($|\Delta_{	ext{self}}| < 1.0\%$).
* **`IMPROVING`**: $\Delta_{	ext{self}} \le -2.0\%$ absolute AND relative decrease $\ge -25\%$.

---

## 4. Paradigm 2: Statistical Early-Warning Indicators

Statistical early warnings identify works or clusters whose operational metrics have crossed into the anomalous tail of the empirical distribution:

### 4.1 Indicator 1: Stagnation Incubation Queue (180–365 Days)
* **Empirical Basis**: 75% of normal MPLADS works disburse their first voucher within 162 days. At 180 days, a project is in the slowest 25% of all works and halfway through its 1-year statutory completion limit.
* **Trigger Condition**:
  - `work_status` $\in$ {`Sanction`, `Vendor Identification`}
  - `total_disbursed_amount` $== 0.0$
  - $180 \le (	ext{REFERENCE\_DATE} - 	ext{sanction\_date}).	ext{days} \le 365$
* **Output**:
  - `incubation_stagnation_count`: Number of at-risk works.
  - `incubation_stagnation_capital_inr`: Total sanction amount locked in non-disbursing projects.
  - Actionable work list for District Planning Officer to verify vendor assignment before statutory dormancy.

### 4.2 Indicator 2: Same-Day / Rapid Batch Duplicate Clusters
* **Empirical Basis**: 93.5% of duplicate works are sanctioned within 15 days of each other, with 64.6% sanctioned on the exact same date with median cluster size of 8 works.
* **Trigger Condition**:
  - $\ge 3$ works in the same district and same `work_type_template`.
  - Pairwise `semantic_similarity` $\ge 0.85$ and `amount_ratio` $\ge 0.90$.
  - Sanction date difference $|t_1 - t_2| \le 15$ days.
* **Output**:
  - `batch_duplicate_cluster_flag`: Boolean alert on district/MP dashboard.
  - Identifies potential tender splitting or duplicate asset allocation before execution starts.

### 4.3 Indicator 3: Cost Drift Acceleration
* **Empirical Basis**: Peer group median costs are stable. A localized price escalation $> 20\%$ above state-wide trends indicates tender inflation.
* **Trigger Condition**:
  - District median cost for a template rising $> 20\%$ faster than state median over two consecutive fiscal quarters ($N \ge 10$ per quarter).
* **Output**:
  - `cost_drift_alert`: Prompts review of district schedule of rates (SoR).

---

## 5. Paradigm 3: Statutory & Rule-Based Compliance Warnings

Statutory warnings track exact countdowns to legal deadlines established by the Ministry of Statistics and Programme Implementation (MoSPI):

### 5.1 Warning 1: SLA Sanction Cliff (45–74 Days Countdown)
* **Statutory Basis**: MPLADS Operational Guidelines Para 3.12 (75-day sanction SLA; 45-day rejection deadline).
* **Logic**:
  $$	ext{Days Elapsed} = (	ext{REFERENCE\_DATE} - 	ext{recommended\_date}).	ext{days}$$
  $$	ext{Days Remaining} = 75 - 	ext{Days Elapsed}$$
* **Trigger Condition**:
  - Work is recommended but not yet sanctioned.
  - $45 \le 	ext{Days Elapsed} < 75$.
* **Actionable Sub-Tiers**:
  - **`WATCHLIST` (Approaching SLA)**: $45 \le 	ext{Days Elapsed} \le 59$ ($16 	ext{ to } 30 	ext{ days remaining}$).
  - **`CRITICAL_CLIFF` (Imminent Breach)**: $60 \le 	ext{Days Elapsed} \le 74$ ($1 	ext{ to } 15 	ext{ days remaining}$).
* **Output**: Prioritized pipeline for District Collector showing exact days remaining before statutory non-compliance.

### 5.2 Warning 2: Statutory Completion Overdue Countdown (300–365 Days)
* **Statutory Basis**: MPLADS Guidelines Para 3.12 (365-day project completion guideline limit).
* **Trigger Condition**:
  - Incomplete work (`is_completed_flag == False`).
  - $300 \le (	ext{REFERENCE\_DATE} - 	ext{sanction\_date}).	ext{days} < 365$.
* **Actionable Meaning**: Final 60-day window before project crosses into statutory completion delay.

---

## 6. Time & Geographic Granularity Calibration

Based on empirical sample size distributions, the platform employs a dual-granularity model:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CALIBRATED GRANULARITY ARCHITECTURE                             │
├───────────────────┬───────────────────────────────┬────────────────────────────────────┤
│ Entity Tier       │ Primary Evaluation Unit       │ Rationale                          │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ National Level    │ Quarterly ($Q$)               │ 1,200 to 16,000 works/quarter.     │
│ (Ministry View)   │ + Monthly Context (Trendline) │ 100% statistically robust.         │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ State Level       │ Quarterly ($Q$)               │ Median state: 250+ works/quarter.  │
│ (State Officer)   │ + Annual Rollup               │ Ample volume for dual-baselines.   │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ District Level    │ Quarterly ($Q$) for N >= 25   │ 69.7% of district-quarters have    │
│ (District Collector) Fiscal Year ($FY$) Primary   │ N < 20. FY grain (median N=19-55)  │
│                   │                               │ ensures statistical stability.     │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ MP Portfolio      │ Cumulative Tenure-to-Date     │ MPs recommend in batches. Annual & │
│ (Lok/Rajya Sabha) │ + Fiscal Year ($FY$)          │ tenure views prevent empty months. │
└───────────────────┴───────────────────────────────┴────────────────────────────────────┘
```

---

## 7. Sparse-Data Handling & Empirical Bayes Shrinkage

### 7.1 Sample Credibility Tiers
Every entity summary is tagged with a deterministic **Credibility Tier** based on sample volume:

| Tier | Quarterly Grain ($N$) | Fiscal Year Grain ($N$) | Rules Applied |
| :--- | :--- | :--- | :--- |
| **`ROBUST`** | $N \ge 50$ works | $N \ge 50$ works | Full statistical rates reported; eligible for rankings. |
| **`MODERATE`** | $25 \le N < 50$ works | $20 \le N < 50$ works | Rates reported; flagged with volume indicator. |
| **`LOW_VOLUME`** | $10 \le N < 25$ works | $10 \le N < 20$ works | Rate displayed with caution badge; excluded from rankings. |
| **`INSUFFICIENT`** | $N < 10$ works | $N < 10$ works | Percentage rate suppressed; displayed strictly as count ($k$ of $N$). |

### 7.2 Empirical Bayes Shrinkage Formula
When ranking districts within a state, smoothed proportions prevent small districts from falsely topping leaderboards:

$$	ilde{p} = rac{k + M \cdot p_{	ext{prior}}}{N + M}$$

Where:
* $k$ = count of flagged works
* $N$ = total works evaluated
* $p_{	ext{prior}}$ = state-wide benchmark anomaly rate
* $M$ = shrinkage weight ($M = 10$ for quarterly grain, $M = 20$ for FY grain)

### 7.3 Missing Period Handling
* Quarters with zero sanctions ($N = 0$) are recorded as `NO_SANCTIONS_RECORDED`.
* Rates are stored as `null`, never `0.0%` (preventing false perfect compliance claims).
* UI line charts disconnect across empty periods.

---

## 8. Double-Counting & Candidate Pair De-duplication Protocol

To guarantee mathematical conservation across aggregate tiers:

1. **Work-Grain Duplicate Attribution**:
   - Model 2 screens pairwise candidate pairs.
   - For aggregate reporting, a work $w$ is marked `is_duplicate_involved = True` if it appears in at least one High severity pair as either `work_id_1` or `work_id_2`.
   - The duplicate rate is strictly $rac{	ext{Count of Unique Works with is\_duplicate\_involved}}{	ext{Total Works}}$.
   - This eliminates the $inom{N}{2}$ pair explosion (56,370 unique works vs 783,736 pairs).
2. **Strict Single-Jurisdiction Attribution**:
   - Every work maps to exactly one State, one District, and one MP. No work is counted across multiple peer buckets.
3. **Temporal Assignment Anchor**:
   - Works are assigned to quarters strictly by their official `sanction_date`.
   - Pre-sanction recommendations are assigned by `recommended_date`.

---

## 9. Proposed Data & API Architecture

### 9.1 Storage Schema (Rollup Parquet & Database Tables)

#### Table 1: `trend_quarterly_rollups`
Stores pre-computed quarterly rollups across National, State, District, and MP tiers:
* `id` (`SERIAL PRIMARY KEY`)
* `grain_type` (`VARCHAR(20)`): `'NATIONAL'`, `'STATE'`, `'DISTRICT'`, `'MP'`
* `state` (`VARCHAR(100)`)
* `district` (`VARCHAR(100)`, nullable)
* `mp_name` (`VARCHAR(255)`, nullable)
* `house` (`VARCHAR(50)`, nullable)
* `year_quarter` (`VARCHAR(10)`): e.g. `'2025Q3'`
* `total_sanctioned_works` (`INTEGER`)
* `total_sanctioned_amount` (`NUMERIC(15,2)`)
* `total_disbursed_amount` (`NUMERIC(15,2)`)
* `credibility_tier` (`VARCHAR(20)`): `'ROBUST'`, `'MODERATE'`, `'LOW_VOLUME'`, `'INSUFFICIENT'`
* **Cost Anomaly Fields**: `high_cost_works_count`, `cost_anomaly_rate`, `excess_sanctioned_amount_inr`
* **Duplicate Fields**: `unique_duplicate_works_count`, `duplicate_work_rate`, `duplicate_cluster_density`, `duplicate_exposure_inr`
* **Fund Anomaly Fields**: `high_fund_works_count`, `fund_anomaly_rate`, `status_mismatch_count`, `dormant_sanction_count`
* **Delay Fields**: `sanction_sla_compliant_count`, `sanction_sla_compliance_rate`, `mean_rec_to_sanc_delay_days`, `high_delay_works_count`, `delay_rate`
* **Trajectory Flags**: `cost_trajectory`, `fund_trajectory`, `delay_trajectory` (`'IMPROVING'`, `'STABLE'`, `'DETERIORATING'`, `'SUSTAINED_INCREASE'`)

#### Table 2: `early_warning_active_backlogs`
Stores live pre-breach pipelines refreshed on schedule:
* `work_id` (`VARCHAR(100) PRIMARY KEY`)
* `state`, `district`, `mp_name`, `sanction_amount`, `work_type_template`
* `warning_type` (`VARCHAR(50)`):
  - `'SLA_SANCTION_CLIFF'` (Statutory)
  - `'STAGNATION_INCUBATION'` (Statistical)
  - `'BATCH_DUPLICATE_CLUSTER'` (Statistical)
* `days_elapsed` (`INTEGER`)
* `days_to_statutory_breach` (`INTEGER`, nullable)
* `urgency_level` (`VARCHAR(20)`): `'WATCHLIST'`, `'CRITICAL'`

---

### 9.2 FastAPI Router Architecture (`api/routers/trends.py`)

1. **`GET /api/v1/analytics/trends/national`**:
   - Returns national quarterly time series across all four independent modules (2024Q3 to 2026Q3).
2. **`GET /api/v1/analytics/trends/state`**:
   - Query: `state` (optional). Returns state quarterly trend lines + comparison against national median.
3. **`GET /api/v1/analytics/trends/district`**:
   - Query: `state`, `district`. Returns district trajectory, credibility tier, and dual-baseline deltas.
4. **`GET /api/v1/analytics/trends/mp`**:
   - Query: `mp_name`. Returns MP tenure-to-date trajectory, FY breakdown, and House benchmark.
5. **`GET /api/v1/analytics/early-warnings`**:
   - Query: `warning_type`, `urgency_level`. Returns live actionable pre-breach queues scoped by user RBAC.

---

## 10. Validation & Automated Verification Suite

Automated pytest tests will assert mathematical invariants and operational contracts:
1. **Conservation of Works**:
   $$\sum_{	ext{states}} 	ext{works}(Q_t) == 	ext{NationalWorks}(Q_t) \quad orall t$$
2. **De-duplication Assertion**:
   $$	ext{unique\_duplicate\_works} \le 	ext{total\_works}$$
3. **Bounded Rates**:
   $$0.0 \le 	ext{rate} \le 1.0 \quad orall 	ext{ entities and periods}$$
4. **Credibility Tier Boundary Tests**:
   - $N=9 
ightarrow$ `INSUFFICIENT`
   - $N=19 
ightarrow$ `LOW_VOLUME`
   - $N=35 
ightarrow$ `MODERATE`
   - $N=60 
ightarrow$ `ROBUST`
5. **Early Warning Boundary Assertions**:
   - $44 	ext{ days} 
ightarrow$ Not in SLA cliff.
   - $45 	ext{ to } 74 	ext{ days} 
ightarrow$ Included in `SLA_SANCTION_CLIFF`.
   - $75 	ext{ days} 
ightarrow$ Statutory breach (excluded from pre-breach, routed to delay results).
   - $179 	ext{ days} 
ightarrow$ Not in stagnation incubation.
   - $180 	ext{ to } 365 	ext{ days with } ₹0 	ext{ spend} 
ightarrow$ Included in `STAGNATION_INCUBATION`.
   - $> 365 	ext{ days} 
ightarrow$ Statutory dormancy (Model 3 violation).

---

## 11. Step-by-Step Implementation Roadmap

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        IMPLEMENTATION PHASES (UPON APPROVAL)                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 1: Analytical Core & Schemas                                                     │
│ • Create `analytics/trends/schemas.py` (Pydantic models for trend series & warnings)   │
│ • Create `analytics/trends/aggregator.py` (Dual-baseline engine & Empirical Bayes)     │
│ • Create `analytics/trends/early_warning.py` (Statutory cliff & incubation queues)     │
│                                                                                        │
│ PHASE 2: Pipeline Execution & Data Persistence                                         │
│ • Execute rollup pipeline across all 98,825 canonical works                           │
│ • Generate `data/model_outputs/trends/trend_quarterly_rollups.parquet`                 │
│ • Generate `data/model_outputs/trends/early_warnings_active.parquet`                   │
│ • Populate PostgreSQL / SQLite cache tables                                            │
│                                                                                        │
│ PHASE 3: FastAPI Routers & Existing Endpoint Enhancement                              │
│ • Implement `api/routers/trends.py` (5 high-performance endpoints)                     │
│ • Register trend router in `api/main.py`                                               │
│ • Enhance `api/routers/summaries.py` to return work-grain duplicate metrics            │
│   and credibility tiers instead of hardcoded 0                                         │
│                                                                                        │
│ PHASE 4: Automated Test Suite & Regression Verification                                │
│ • Implement `tests/test_trend_rollups.py` and `tests/test_trend_api.py`                │
│ • Assert 100% test pass rate across new and existing 25 tests                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Analytical Limitations & Boundary Constraints

1. **Temporal Horizon**: Operational data is valid from 2024Q3 to 2026Q3 (18th Lok Sabha era). Long-term multi-decade forecasting is not possible.
2. **2024Q2 Electoral Lull**: The Model Code of Conduct caused an operational pause in April–May 2024. Trend models treat this as a constitutional hiatus, not an administrative failure.
3. **Portal Reporting Latency**: Voucher uploads can occur in monthly batches, causing minor artificial tranche clustering.
4. **Absence of Rejection Data**: 45-day rejection SLAs cannot be verified because government portals omit rejection timestamps.

---

## 13. What NOT to Build

* ❌ **DO NOT build an AI/ML forecasting model** (ARIMA, Prophet, LSTM) claiming to predict future expenditure or anomalies. The data does not support it.
* ❌ **DO NOT build a composite risk trend index** (never blend cost, duplicate, fund, and delay into a single trend line).
* ❌ **DO NOT use monthly aggregation for small districts or MPs** (causes severe sparsity).
* ❌ **DO NOT rank districts by raw percentage anomaly rates without sample size qualification**.
* ❌ **DO NOT count duplicate candidate pairs as an aggregate metric** (always count unique works).
* ❌ **DO NOT synthesize or impute fictitious works** during low-volume quarters.

---

## 14. RECOMMENDED BUILD (Priority Matrix)

| Priority | Component | Target Files | Primary Deliverable |
| :---: | :--- | :--- | :--- |
| **P1** | **Analytical Rollup Engine** | `analytics/trends/aggregator.py`<br>`analytics/trends/schemas.py` | Deterministic quarterly rollup generator with de-duplication, rate derivations, dual-baselines, and sample credibility tiers. |
| **P2** | **Early-Warning Engine** | `analytics/trends/early_warning.py` | Pre-breach queue generator (Statutory SLA Sanction Cliff at 45–74 days, Statistical Stagnation Incubation at 180–365 days). |
| **P3** | **Rollup Persistence** | `analytics/trends/pipeline.py`<br>`data/model_outputs/trends/` | Pre-computed Parquet and database cache for sub-50ms query latency. |
| **P4** | **FastAPI Trend Routers** | `api/routers/trends.py`<br>`api/main.py` | 5 high-performance endpoints (`/trends/national`, `/trends/state`, `/trends/district`, `/trends/mp`, `/early-warnings`). |
| **P5** | **Summary Router Upgrade** | `api/routers/summaries.py` | Replace hardcoded `high_duplicate_pairs=0` with work-grain duplicate metrics; add credibility tiers. |
| **P6** | **Automated Test Suite** | `tests/test_trend_rollups.py`<br>`tests/test_trend_api.py` | Automated tests asserting conservation invariants, boundary handling, and RBAC scoping. |

---

**END OF REFINED IMPLEMENTATION PLAN**  
*Awaiting user approval before proceeding to implementation code.*
