# Phase 3 — Feature Engineering & Feature Quality Report
**Status**: `PHASE 3 COMPLETE`  

---

## 1. Feature Registry & Model Mapping

| Feature Name | Used By | Unit of Analysis | Formula / Derivation | Leakage Control | Status |
|---|---|---|---|---|---|
| `sanction_amount_log` | Model 1 (Cost Anomaly) | `work` | `log(1 + sanction_amount)` | None (Sanction-time feature) | `INCLUDED` |
| `peer_iqr_deviation` | Model 1 (Cost Anomaly) | `work` | `(sanction_amount - peer_median) / (peer_iqr / 1.349)` | None (Sanction-time feature) | `INCLUDED` |
| `cost_ratio_vs_peer_median` | Model 1 (Cost Anomaly) | `work` | `sanction_amount / peer_median_amount` | None (Sanction-time feature) | `INCLUDED` |
| `is_data_quality_exception` | Model 1 (Cost Anomaly) & DQ Routing | `work` | `0 < sanction_amount < 1000` | None | `INCLUDED` |
| `days_diff` | Model 2 (Duplicate Detection) | `work_pair` | `abs(sanction_date_1 - sanction_date_2).days` | None | `INCLUDED` |
| `amount_ratio` | Model 2 (Duplicate Detection) | `work_pair` | `min(amt1, amt2) / max(amt1, amt2)` | None | `INCLUDED` |
| `utilization_ratio` | Model 3 (Expenditure Anomaly) & Logic 2 | `work` | `min(1.00, sum(fund_disbursed) / sanction_amount)` | Post-sanction (Model 3 only) | `INCLUDED` |
| `payment_concentration_hhi` | Model 3 (Expenditure Anomaly) | `work` | `sum((tranche_amount / total_disbursed)^2)` | Post-sanction (Model 3 only) | `INCLUDED` |
| `total_disbursed_amount_monthly` | Model 4 (Expenditure Forecasting) | `state_month` | `sum(fund_disbursed_amount) per State and Month` | None (Historical time series) | `INCLUDED` |
| `rec_to_sanc_sla_exceeded_flag` | Logic 1 (Delay & SLA Logic) | `work` | `rec_to_sanc_days > 75` | None | `INCLUDED` |
| `entitlement_exceeded_flag` | Logic 3 (Compliance Rule Engine) | `mp` | `sum(sanction_amount) > allocated_amount` | None | `INCLUDED` |
| `ida_vendor_hhi` | Vendor-Agency Risk Analyzer | `ida` | `sum((vendor_ida_disbursed / ida_total_disbursed)^2)` | None | `INCLUDED` |

---

## 2. Explicitly Rejected Candidate Features

| Candidate Feature | Status | Reason Rejected |
|---|---|---|
| `physical_progress_percentage` | `REJECTED` | No numeric physical-progress percentage field exists in any raw or processed MPLADS dataset. |
| `intraday_payment_velocity` | `REJECTED` | Expenditure timestamps supply transaction dates only, not intraday time of day. |
| `literal_cost_overrun_amount` | `REJECTED` | Disbursement is strictly capped at sanctioned ceiling (utilization <= 1.00). Replaced by Utilization Gap and Re-sanction rules. |
| `sc_st_beneficiary_earmark_pct` | `REJECTED` | No caste or beneficiary category field exists in raw CSV datasets. |

---

## 3. Feature Coverage & Quality Diagnostics Summary

### Table: `cost_anomaly_features` (98,825 rows, 22 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `sanction_amount` | 98,825 | 0.0% | 2.46 | ₹73,500,000.00 | ₹358,426.00 | 20.35 |
| `sanction_amount_log` | 98,825 | 0.0% | 1.24 | ₹18.11 | ₹12.79 | -0.33 |
| `rec_to_sanc_days` | 98,825 | 0.0% | 0.00 | ₹1,100.00 | ₹77.00 | 1.98 |
| `desc_char_len` | 98,825 | 0.0% | 0.00 | ₹500.00 | ₹84.00 | 1.92 |
| `desc_word_count` | 98,825 | 0.0% | 0.00 | ₹101.00 | ₹13.00 | 1.91 |
| `peer_group_size` | 98,825 | 0.0% | ₹15.00 | ₹98,825.00 | ₹663.00 | 18.41 |
| `peer_median_amount` | 98,825 | 0.0% | ₹20,000.00 | ₹3,393,546.00 | ₹399,960.00 | 1.98 |
| `peer_iqr_amount` | 98,825 | 0.0% | 1.00 | ₹11,435,075.00 | ₹220,015.00 | 7.23 |
| `peer_iqr_deviation` | 98,825 | 0.0% | ₹-8,390.00 | ₹216,270.00 | 0.00 | 90.45 |
| `cost_ratio_vs_peer_median` | 98,825 | 0.0% | 0.00 | ₹1,111.73 | 1.00 | 76.38 |


### Table: `duplicate_candidate_pairs` (1,803,361 rows, 22 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `days_diff` | 1,803,361 | 0.0% | 0.00 | ₹90.00 | 1.00 | 1.41 |
| `sanction_amount_1` | 1,803,361 | 0.0% | ₹10,000.00 | ₹73,500,000.00 | ₹107,771.00 | 33.49 |
| `sanction_amount_2` | 1,803,361 | 0.0% | ₹10,000.00 | ₹73,500,000.00 | ₹107,771.00 | 36.35 |
| `amount_diff_abs` | 1,803,361 | 0.0% | 0.00 | ₹6,000,000.00 | 0.00 | 181.27 |
| `amount_ratio` | 1,803,361 | 0.0% | 0.90 | 1.00 | 1.00 | -4.47 |


### Table: `expenditure_anomaly_features` (98,825 rows, 30 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `sanction_amount` | 98,825 | 0.0% | 2.46 | ₹73,500,000.00 | ₹358,426.00 | 20.35 |
| `total_disbursed_amount` | 98,825 | 0.0% | 0.00 | ₹71,238,651.00 | ₹200,000.00 | 24.10 |
| `transaction_count` | 98,825 | 0.0% | 0.00 | ₹191.00 | 1.00 | 20.06 |
| `max_single_payment` | 71,928 | 27.22% | ₹3,000.00 | ₹32,562,250.00 | ₹299,170.00 | 11.96 |
| `mean_single_payment` | 71,928 | 27.22% | ₹2,496.00 | ₹32,562,250.00 | ₹250,000.00 | 10.85 |
| `vendor_count` | 98,825 | 0.0% | 0.00 | ₹44.00 | 1.00 | 10.35 |
| `payment_success_count` | 71,928 | 27.22% | 0.00 | ₹191.00 | 1.00 | 21.04 |
| `payment_inprogress_count` | 71,928 | 27.22% | 0.00 | ₹32.00 | 0.00 | 34.81 |
| `max_payment_ratio` | 71,928 | 27.22% | 0.02 | 1.00 | 1.00 | -1.86 |
| `spending_window_days` | 71,928 | 27.22% | 0.00 | ₹933.00 | 0.00 | 3.00 |
| `spending_velocity_per_day` | 71,928 | 27.22% | ₹73.41 | ₹35,321,457.00 | ₹202,016.00 | 12.46 |
| `payment_concentration_hhi` | 98,825 | 0.0% | 0.00 | 1.00 | 1.00 | -0.95 |
| `tranche_concentration_hhi` | 98,825 | 0.0% | 0.00 | 1.00 | 1.00 | -0.61 |
| `utilization_ratio` | 98,825 | 0.0% | 0.00 | 1.00 | 1.00 | -0.85 |
| `remaining_sanction_balance` | 98,825 | 0.0% | 0.00 | ₹44,000,000.00 | ₹250.00 | 19.00 |
| `days_to_first_disbursement` | 71,928 | 27.22% | 0.00 | ₹900.00 | ₹72.00 | 1.39 |


### Table: `monthly_forecasting_series` (1,365 rows, 6 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `total_disbursed_amount` | 1,365 | 0.0% | 0.00 | ₹555,625,826.00 | ₹4,458,289.00 | 4.14 |
| `transaction_count` | 1,365 | 0.0% | 0.00 | ₹1,701.00 | 7.00 | 4.26 |
| `active_works_count` | 1,365 | 0.0% | 0.00 | ₹1,628.00 | 5.00 | 5.12 |


### Table: `deterministic_logic_features` (98,825 rows, 18 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `sanction_amount` | 98,825 | 0.0% | 2.46 | ₹73,500,000.00 | ₹358,426.00 | 20.35 |
| `total_disbursed_amount` | 98,825 | 0.0% | 0.00 | ₹71,238,651.00 | ₹200,000.00 | 24.10 |
| `utilization_ratio` | 98,825 | 0.0% | 0.00 | 1.00 | 1.00 | -0.85 |
| `rec_to_sanc_days` | 71,928 | 27.22% | 0.00 | ₹900.00 | ₹72.00 | 1.39 |
| `rec_to_sanc_sla_delay_days` | 98,825 | 0.0% | 0.00 | ₹825.00 | 0.00 | 2.57 |
| `days_since_sanction_snapshot` | 98,825 | 0.0% | 1.00 | ₹1,157.00 | ₹344.00 | 0.61 |
| `completion_sla_delay_days` | 98,825 | 0.0% | 0.00 | ₹792.00 | 0.00 | 2.55 |
| `utilization_gap_amount` | 98,825 | 0.0% | 0.00 | ₹41,678,747.00 | 0.00 | 79.10 |


### Table: `compliance_rule_features` (774 rows, 11 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `allocated_amount` | 774 | 0.0% | 0.00 | ₹327,477,390.86 | ₹147,000,000.00 | -0.23 |
| `cumulative_sanctioned_amount` | 774 | 0.0% | 0.00 | ₹220,854,384.00 | ₹79,016,199.40 | 0.33 |
| `sanctioned_works_count` | 774 | 0.0% | 0.00 | ₹1,383.00 | ₹91.00 | 2.46 |
| `entitlement_utilization_pct` | 774 | 0.0% | 0.00 | ₹99.96 | ₹51.13 | -0.38 |
| `entitlement_excess_amount` | 774 | 0.0% | 0.00 | 0.00 | 0.00 | 0.00 |
| `calamity_consent_amount` | 774 | 0.0% | 0.00 | ₹10,000,000.00 | 0.00 | 7.31 |


### Table: `ida_vendor_pair_features` (30,543 rows, 12 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `vendor_ida_transaction_count` | 30,543 | 0.0% | 1.00 | ₹789.00 | 1.00 | 19.83 |
| `vendor_ida_total_disbursed` | 30,543 | 0.0% | 4.00 | ₹158,392,245.00 | ₹399,928.00 | 13.78 |
| `distinct_works_count` | 30,543 | 0.0% | 1.00 | ₹785.00 | 1.00 | 23.84 |
| `distinct_mps_count` | 30,543 | 0.0% | 1.00 | 7.00 | 1.00 | 6.65 |
| `ida_total_disbursed` | 30,543 | 0.0% | ₹164,000.00 | ₹611,079,504.00 | ₹51,601,177.00 | 2.50 |
| `vendor_share_in_ida` | 30,543 | 0.0% | 0.00 | 1.00 | 0.01 | 7.87 |
| `ida_vendor_hhi` | 30,543 | 0.0% | 0.01 | 1.00 | 0.04 | 3.69 |


### Table: `vendor_national_features` (28,329 rows, 7 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `vendor_total_disbursed_national` | 28,329 | 0.0% | ₹58.00 | ₹254,451,848.00 | ₹400,000.00 | 16.82 |
| `vendor_total_transactions_national` | 28,329 | 0.0% | 1.00 | ₹1,271.00 | 1.00 | 27.35 |
| `vendor_distinct_ida_count` | 28,329 | 0.0% | 1.00 | ₹21.00 | 1.00 | 13.36 |
| `vendor_distinct_mp_count` | 28,329 | 0.0% | 1.00 | ₹29.00 | 1.00 | 14.34 |
| `vendor_distinct_works_count` | 28,329 | 0.0% | 1.00 | ₹785.00 | 1.00 | 24.64 |


### Table: `ida_hhi_summary` (765 rows, 6 columns)
| Numeric Feature | Non-Null Count | Null % | Min | Max | Median | Skewness |
|---|---|---|---|---|---|---|
| `ida_total_disbursed` | 765 | 0.0% | ₹164,000.00 | ₹611,079,504.00 | ₹33,109,962.00 | 3.40 |
| `vendor_count_in_ida` | 765 | 0.0% | 1.00 | ₹566.00 | ₹21.00 | 4.24 |
| `ida_vendor_hhi` | 765 | 0.0% | 0.01 | 1.00 | 0.13 | 1.83 |

