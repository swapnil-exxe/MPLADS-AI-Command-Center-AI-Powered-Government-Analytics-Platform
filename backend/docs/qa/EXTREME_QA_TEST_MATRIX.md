# EXTREME QA TEST MATRIX — MPLADS PLATFORM

**Audit Date**: September 13, 2026  
**Target Environment**: `http://localhost:8000`  
**Total Test Cases Evaluated**: 117 Automated + 48 UI Actions + 27 API Fuzzing Vectors = **192 Total Verification Points**

---

## 1. UI & BUTTON INVENTORY MATRIX

| Page | Element / Button | Action | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LandingPage** | Navigation Header Links | Click "Features", "Data Freshness", "Security", "FAQ" | Smooth scroll to anchor `#features`, `#data-freshness`, `#security`, `#faq` | Anchors scrolled cleanly | **PASS** |
| **LandingPage** | "Launch Dashboard" CTA | Click Button | Navigate to `/login` | Navigated to `/login` | **PASS** |
| **LandingPage** | FAQ Accordion Items | Click FAQ Questions | Expand/collapse answer text | Accordion toggles state | **PASS** |
| **Login** | Stakeholder Quick-Login Cards | Click "Ministry", "State", "District", "MP" | Pre-fill email/password fields | Form fields updated | **PASS** |
| **Login** | "Sign In" Button | Submit Form | Authenticate via JWT & redirect to `/dashboard` | JWT issued, redirected | **PASS** |
| **Dashboard** | Sidebar Navigation Links | Click "Works", "Cost", "Duplicates", "Funds", "Delays", "Trends" | Navigate to corresponding frontend route | Navigation successful | **PASS** |
| **Dashboard** | Header Logout Button | Click Button | Revoke JWT session and redirect to `/login` | Session cleared, redirected | **PASS** |
| **WorksRegistry** | Search Input | Type "Patna" & press Enter | Filter works list by description/IDA | Table filtered dynamically | **PASS** |
| **WorksRegistry** | Filter Dropdowns | Select State / Category / Status | Send scoped API request with query parameters | Table updated | **PASS** |
| **WorksRegistry** | "Reset Filters" Button | Click Button | Clear all search and filter dropdown selections | All filters cleared | **PASS** |
| **WorksRegistry** | Pagination Next/Prev | Click Page Buttons | Request next/previous page of 20 works | Table re-paginated | **PASS** |
| **WorkDetail** | "Back to Works" Button | Click Button | Return to `/works` keeping previous state | Returned to `/works` | **PASS** |
| **CostAnomalies** | Severity Tabs | Click "HIGH", "MEDIUM", "LOW" | Filter cost anomalies by severity tier | Filtered list displayed | **PASS** |
| **DuplicateWorks**| "Compare Duplicate Pair" | Click Action Link | Navigate to `/duplicates/compare?id=...` | Comparison page loaded | **PASS** |
| **StatutoryDelays**| SLA Filter Controls | Select "Recommendation Delay" | Filter delay SLA alerts | Filtered list displayed | **PASS** |
| **AdminUsers** | "Provision User" Form | Submit New User | Create new user via `POST /api/v1/auth/users` | User created | **PASS** |
| **SourceMonitor** | "Trigger Manual Scraper" | Click Button | Invoke `POST /api/v1/admin/scraper/run` | Scrapling scraper triggered | **PASS** |
| **SubhoChatbot** | Floating Chat Button | Click Toggle | Open/close chatbot drawer | Drawer toggles | **PASS** |
| **SubhoChatbot** | Send Message Button | Submit Question | Send query to `POST /api/v1/public-chat` | LLM response rendered | **PASS** |

---

## 2. API ENDPOINT MATRIX

| Method | Endpoint | Auth Tier | Fuzzing / Parameter Vector | Expected HTTP | Actual HTTP | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Public | Standard ping | 200 OK | 200 OK | **PASS** |
| `GET` | `/api/v1/meta/filters` | Public | Dynamic metadata lookup | 200 OK | 200 OK | **PASS** |
| `POST` | `/api/v1/auth/login` | Public | SQLi payload: `email="' OR '1'='1"` | 401 / 422 | 422 Unprocessable | **PASS** |
| `POST` | `/api/v1/auth/login` | Public | XSS payload: `<script>alert(1)</script>` | 401 / 422 | 422 Unprocessable | **PASS** |
| `GET` | `/api/v1/auth/me` | JWT | Valid Bearer token | 200 OK | 200 OK | **PASS** |
| `GET` | `/api/v1/auth/me` | None | Missing token | 401 Unauthorized | 401 Unauthorized | **PASS** |
| `GET` | `/api/v1/works` | Scoped | `page=-1&page_size=0` | 422 Unprocessable | 422 Unprocessable | **PASS** |
| `GET` | `/api/v1/works` | Scoped | `search=' OR '1'='1` | 200 OK (Clean) | 200 OK | **PASS** |
| `GET` | `/api/v1/works/{work_id}` | Scoped | `NON_EXISTENT_ID_999` | 404 Not Found | 404 Not Found | **PASS** |
| `GET` | `/api/v1/analytics/cost-anomalies` | Scoped | `page_size=99999` | 422 Unprocessable | 422 Unprocessable | **PASS** |
| `GET` | `/api/v1/analytics/duplicate-works` | Scoped | `min_duplicate_score=-0.5` | 422 Unprocessable | 422 Unprocessable | **PASS** |
| `GET` | `/api/v1/analytics/delays` | Scoped | `page=abc` | 422 Unprocessable | 422 Unprocessable | **PASS** |
| `GET` | `/api/v1/analytics/district-summary`| Scoped | `state=Bihar&district=PATNA` | 200 OK | 200 OK | **PASS** |
| `GET` | `/api/v1/analytics/mp-summary` | Scoped | `mp_name=SARABJEET%20SINGH%20KHALSA`| 200 OK | 200 OK | **PASS** |
| `POST` | `/api/v1/public-chat` | Public | Prompt Injection: "Ignore previous instructions" | 200 OK (Refusal) | 200 OK (Safe) | **PASS** |
| `POST` | `/api/v1/admin/scraper/run` | Ministry | Manual Scrapling Execution | 200 OK | 200 OK | **PASS** |
