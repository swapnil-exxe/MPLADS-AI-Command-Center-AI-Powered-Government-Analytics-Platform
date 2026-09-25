# 13. Comprehensive Automated Test Suite & QA

## Automated Test Suite Architecture (`tests/`)

The platform contains a test suite of **117 automated tests** across 15 test files with a **100% pass rate**:

### Test Suites Summary

- `test_api.py` (15 tests): Core REST API endpoints and dossiers.
- `test_auth_rbac.py` (19 tests): Login authentication, timing defense, JWT verification, and 4 stakeholder RBAC scopes.
- `test_database_ingestion.py` (6 tests): Database connections, table schemas, and foreign key integrity.
- `test_delay_rules.py` (7 tests): SLA thresholds (75d & 365d) and open work aging.
- `test_feature_engineering.py` (10 tests): Canonical building, zero leakage, and candidate blocking.
- `test_model1_cost_anomaly.py` (6 tests): Peer Group Isolation Forest scoring.
- `test_model2_duplicate_work.py` (6 tests): Sentence Transformer similarity scoring.
- `test_model3_fund_expenditure.py` (6 tests): Cohort Isolation Forest and HHI concentration.
- `test_pipeline.py` (10 tests): Currency, date, and string cleaners.
- `test_scraper.py` (4 tests): Spider requests and change detection.
- `test_subho_chatbot.py` (3 tests): Chatbot injection defenses and fallback responses.
- `test_trend_api.py` & `test_trend_rollups.py` (15 tests): Quarterly trend analytics.

