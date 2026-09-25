# 20. Final One-Page Reference Cheat Sheet

## One-Page Project Master Reference

- **Project Name**: MPLADS AI Command Center (Governance & Analytics Platform)
- **Platform Requirement**: MPLADS Governance & Analytics Platform (MoSPI)
- **Core Scope**: 190,942 Master Works | 109,311 Expenditure Vouchers | ₹10,211.49 Cr Sanctioned | 773 Districts | 36 States
- **Stack**: React 18 SPA + Vite + Tailwind | FastAPI + Async Uvicorn | Supabase PostgreSQL 17.6 | PyArrow & Apache Parquet
- **4 Models**:
  1. Cost Anomaly: Hierarchical Peer Isolation Forest (`n_estimators=100`, Sigmoid calibrated)
  2. Duplicate Work: `all-MiniLM-L6-v2` dense embeddings + Structural proximity + 90d Candidate Blocking
  3. Fund Anomaly: Active spend Isolation Forest + HHI concentration + Status Mismatch rules
  4. Delay SLA: Rule Engine enforcing 75-day sanction (Para 3.12) & 365-day completion SLAs against `2026-09-05`
- **Security**: OAuth2 JWT (`HS256`), Bcrypt 12 rounds, `DUMMY_BCRYPT_HASH` timing attack defense, 4 RBAC Tiers (`MINISTRY`, `STATE_OFFICER`, `DISTRICT_OFFICER`, `MP`), Composite District Scoping `(state, district)`.
- **Validation**: 117/117 Automated Tests Passing (100% Pass Rate). 0 Critical Vulnerabilities.

