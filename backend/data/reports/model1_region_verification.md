# Model 1 Peer Hierarchy & Region Verification Report

**Project**: AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)  
**Verification Target**: Model 1 (Anomalous Cost Estimate Detector) Peer Hierarchy & Region Field Availability  
**Evaluation Date**: 2026-09-07  

---

## 1. Region Availability

```text
REGION DATA: NOT AVAILABLE
```

No authoritative region field, regional zone classification, or explicit state-to-region mapping exists anywhere in the raw data, processed datasets, feature layers, or project configuration files.

---

## 2. Evidence

A thorough, multi-layer inspection was conducted across all codebase components, data files, and configuration dictionaries:

### 2.1 Datasets Inspected
1. **Raw Source CSVs** (`data/original/LokSabha18/`, `data/original/RajyaSabha_Sitting/`):
   * Columns present in raw data: `State`, `IDA`, `Constituency` (Lok Sabha only), `Hon'ble Members of Parliament`, `Work`, `Work Category`, `Work Description`, `Recommended date`, `RECOMMENDED AMOUNT ( ₹ )`, `Sanction Date`, `Sanction Amount ( ₹ )`, `Work Status`, `Completion Date`, `Amount Disbursed ( ₹ )`, `Expenditure Date`, `Vendor Name`, `Payment Status`, `Fund Disbursed Amount ( ₹ )`, `Allocated Amount ( ₹ )`, `Calamity Type`, `Calamity Name`, `Date of Consent`, `Consent Amount ( ₹ )`.
   * Occurrences of the string `"region"` in the raw data appear **exclusively within free-text unstructured descriptions** (e.g., *"improvements to street in Karaikal region"*, *"Regional Cancer Centre"*, *"Regional Development office"*). There is no structured regional metadata column.
2. **Phase 2 Cleaned Parquet Datasets** (`data/processed/`):
   * Verified all 12 active Parquet files (`works_sanctioned`, `works_recommended`, `works_completed`, `expenditures`, `mp_allocations`, `calamity` across `LokSabha18` and `RajyaSabha_Sitting`).
   * Geographic fields present: `state`, `ida`, `district` (extracted from IDA), and `constituency` (Lok Sabha only).
   * Schema scan for keyword tokens `["region", "zone", "east", "west", "north", "south", "central"]` returned **0 matching columns**.
3. **Phase 3 Feature & Canonical Layers** (`data/features/`):
   * `data/features/shared/canonical_works.parquet` (98,825 rows) contains geographic fields `state`, `district`, `ida`, and `constituency_or_term`.
   * `data/features/cost/cost_anomaly_features.parquet` contains `state`, `district`, `ida`, and `constituency_or_term`.
   * No `region` or `zone` column exists in any feature table.
4. **Configuration & Data Dictionaries**:
   * `data_pipeline/config.py`: `COLUMN_CANONICAL_MAP` standardizes all source headers; no regional column exists.
   * `data_pipeline/geography.py`: Solely extracts `district` from `ida`.
   * `feature_engineering/feature_registry.py` and `feature_quality_report.json`: Document all engineered features; no regional groupings or mappings exist.

### 2.2 Feasibility of Deriving Region from Existing Geography Fields
* Existing geography fields: `state`, `district`, `ida`, `constituency_or_term`.
* In accordance with explicit system design constraints:
  * No ad-hoc regional grouping (such as assuming *Uttar Pradesh → North* or *Maharashtra → West*) may be invented without an authoritative, published policy standard (such as official Ministry of Home Affairs Zonal Council definitions or MoSPI regional zones).
  * Because no such authoritative mapping table currently exists in the project repository or dataset bundle, Region **cannot currently be derived reliably**.

---

## 3. Work Type Verification

The `work_type_template` field was inspected across the active dataset of 98,825 sanctioned works:

* **Source Field & Extraction**:
  * In Phase 2 (`data_pipeline/work_id.py`), `work_type_template` is systematically extracted from the standard administrative prefix of the raw `Work` / `Work ID` string:
    * Standard works: `WS/MP<number>/<year>/<serial>-<work_type_template>`
    * Unnumbered recommendations: `NA-<work_type_template>`
* **Number of Unique Work Types**:
  * Exactly **115 unique work types** exist across the entire active canonical layer.
* **Unclassified / Null Records**:
  * Null count: **0** (0.00%)
  * Explicit `"UNCLASSIFIED"` count: **0** (0.00%)
  * Every single sanctioned work (100.0%) has a populated, valid work-type template.
* **Consistency Across Parliamentary Houses**:
  * **Lok Sabha 18** (79,219 works): 112 unique work-type templates; 0 nulls.
  * **Rajya Sabha Sitting** (19,606 works): 101 unique work-type templates; 0 nulls.
  * The top categories align identically across both houses (e.g., Road & link road construction, public space lighting, street lighting, community halls, tube-wells, mobile water tankers).

---

## 4. Current Peer Hierarchy Implementation & Coverage

The current Model 1 peer-group assigner (`ml_models/cost_anomaly/peer_groups.py`) implements a deterministic 3-tier fallback with a minimum group size threshold of $N \ge 15$:

$$\text{State} \times \text{Work Type} \longrightarrow \text{National Work Type} \longrightarrow \text{National Overall}$$

### Actual Coverage & Group Counts (Total: 98,825 Sanctioned Works)

| Hierarchy Level | Works Covered | Pct of Total | Unique Groups | Min Group Size | Max Group Size | Fallback Condition ($N \ge 15$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1: `STATE_WORK_TYPE`** | 94,249 | 95.37% | 561 | 15 | 6,964 | Primary level; satisfied for 95.4% of works |
| **Tier 2: `NATIONAL_WORK_TYPE`** | 4,466 | 4.52% | 89 | 15 | 24,132 | Fallback tier; State group had $N < 15$ |
| **Tier 3: `NATIONAL_OVERALL`** | 110 | 0.11% | 1 | 98,825 | 98,825 | National catch-all; Work Type had $N < 15$ |
| **Total Scored Works** | **98,825** | **100.00%** | **651** | **15** | **98,825** | **Strict $N \ge 15$ rule: 0 violations** |

* **Group Size Compliance**: Exactly 0 works belong to peer groups with $N < 15$.
* **Isolation Forest Models**: 649 distinct peer Isolation Forest models were trained and persisted under `models/cost_anomaly/peer_models/` (covering 561 `STATE_WORK_TYPE` groups, 87 `NATIONAL_WORK_TYPE` groups, and 1 `NATIONAL_OVERALL` group).

---

## 5. Recommendation

1. **Retain Current Peer Hierarchy for Model 1**:
   * The current fallback hierarchy (`State × Work Type` $\rightarrow$ `National Work Type` $\rightarrow$ `National Overall`) successfully places **95.37%** of works directly into fine-grained local state-category peer groups, and **4.52%** into national category peer groups.
   * Only **0.11%** (110 works out of 98,825) require the global national fallback.
2. **Do Not Implement Region at this Stage**:
   * Introducing an invented or heuristic state-to-region mapping without an authoritative government classification would introduce arbitrary bias into cost baselines.
   * If an authoritative external zone definition (e.g., Zonal Councils under the States Reorganisation Act: Northern, Central, Eastern, Western, Southern, North-Eastern) is officially approved in a later phase, it can be introduced cleanly as an intermediate tier between State and National Work Type without altering Model 1's mathematical design.

---

## 6. Unit Test Verification

The Model 1 test suite was executed against the current implementation:

```bash
py -3.12 -m pytest tests/test_model1_cost_anomaly.py -v
```

### Test Results
```text
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-9.1.1, pluggy-1.6.0 -- C:\Program Files\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\zaid\Desktop\MPLADS_Analytics
collecting ... collected 6 items

tests/test_model1_cost_anomaly.py::test_model1_input_schema_validation PASSED [ 16%]
tests/test_model1_cost_anomaly.py::test_model1_zero_leakage_assertion PASSED [ 33%]
tests/test_model1_cost_anomaly.py::test_model1_peer_group_hierarchy_and_fallback PASSED [ 50%]
tests/test_model1_cost_anomaly.py::test_model1_score_bounds_and_determinism PASSED [ 66%]
tests/test_model1_cost_anomaly.py::test_model1_data_quality_exception_routing PASSED [ 83%]
tests/test_model1_cost_anomaly.py::test_model1_end_to_end_pipeline_output PASSED [100%]

============================== 6 passed in 6.10s ==============================
```

All 6 unit tests passed with 100% success.

---

**MODEL 1 REGION VERIFICATION COMPLETE**