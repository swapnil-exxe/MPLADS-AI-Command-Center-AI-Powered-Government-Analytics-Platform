# Ministry Dashboard & Navigation UX Redesign Plan
## PS 190942 — AI-Powered MPLADS Monitoring & Anomaly Detection System

**Document Version:** 2.0  
**Scope:** Frontend presentation layer only — zero backend/API/database changes  
**Source of Truth:** Actual implemented codebase, not aspirational features  

---

## 1. PS 190942 vs. Current Implementation — Honest Gap Analysis

Before making any design changes, here is an honest mapping of what the PS asks for against what our system actually provides.

| PS 190942 Requirement | What We Actually Have | Dashboard Treatment |
| :--- | :--- | :--- |
| **Detect anomalies in cost estimates** | ✅ Model 1: Isolation Forest + Peer-Group IQR | Surface HIGH count on dashboard, link to full investigation page |
| **Detect duplicate works** | ✅ Model 2: MiniLM Semantic Embeddings + Multi-Attribute Blocking | Surface HIGH count on dashboard, link to pair comparison page |
| **Detect fund utilization anomalies** | ✅ Model 3: Vendor HHI + Disbursement Dormancy + Utilization Ratio | Surface HIGH count on dashboard, link to financial audit page |
| **Detect delays and SLA breaches** | ✅ Model 4: Rule Engine — 75d Sanction SLA, 365d Completion SLA, Open Work Aging | Surface HIGH count on dashboard, link to SLA tracking page |
| **Decision-support dashboards for 4 stakeholder tiers** | ✅ Role-switched Dashboard component (Ministry/State/District/MP views) | Redesign Ministry view; State/District/MP views functional |
| **Risk-based alerts** | ⚠️ Partial — Severity levels (HIGH/MEDIUM/LOW) exist per model | Surface HIGH-severity items in "Attention Required" queue — no push notifications |
| **Automated compliance monitoring** | ⚠️ Partial — Only Statutory Delay SLA compliance (Para 3.12: 75d recommendation→sanction) | Label honestly as "Statutory Delay Compliance", not "Compliance Engine" |
| **Trend analysis** | ❌ No time-series API endpoints. Works table has dates but no grouped/time-bucketed endpoint | Mark as limitation; descriptive only if added client-side |
| **Predictive insights / early warning** | ❌ No forecasting model exists | Do NOT claim or simulate predictions |
| **Composite risk scoring** | ❌ Intentionally absent — 4 models are independent by design | Do NOT introduce; this is a deliberate architectural choice |

> [!IMPORTANT]
> **Honesty principle**: The dashboard must never imply capabilities we don't have. No "Predictive Insights", no "AI Forecast", no "Compliance Engine", no composite risk scores. Use precise language that maps to actual implemented functionality.

---

## 2. Current Ministry Dashboard — Problems Identified

Based on inspection of [Dashboard.tsx](file:///c:/Users/zaid/Desktop/MPLADS_Analytics/frontend/src/pages/Dashboard.tsx) and the current screenshot:

### 2.1 Information Architecture Problems

| # | Problem | Impact |
| :--: | :--- | :--- |
| 1 | **Redundant double row**: 4 metric cards + 4 navigation cards = 8 cards for 4 models | Visual clutter; unclear what is actionable vs. informational |
| 2 | **Missing macro-financial context**: No total sanctioned (₹5,431 Cr), disbursed (₹2,260 Cr), or utilization rate (41.6%) prominently displayed | Ministry official can't see the financial big picture at a glance |
| 3 | **Metric cards show text instead of numbers**: Cards 2-4 show "Requires Review", "Semantic Pairs", "75d SLA Compliance" instead of actual HIGH counts (986, 50k, 15,263) | Evaluator cannot assess scale of issues |
| 4 | **No state-level view**: Ministry oversees 36 States/UTs but dashboard shows district-level data with no state aggregation | Missing the primary geographic oversight level for Ministry |
| 5 | **Arbitrary district chart**: Bar chart shows "first 7 districts" without strategic sorting — doesn't answer any decision question | Decorative rather than decision-supporting |
| 6 | **Single-model priority queue**: Only shows delays ranking — ignores cost, duplicate, and fund findings | Incomplete attention signal |
| 7 | **No cross-model attention surface**: No way to see which works/districts have HIGH findings across multiple models simultaneously | Misses the most urgent cases requiring multi-dimensional investigation |

### 2.2 Visual/UX Problems

| # | Problem | Impact |
| :--: | :--- | :--- |
| 8 | **Dark sidebar vs. light content**: Jet-black bg-slate-900 sidebar creates harsh contrast | Looks unintegrated; not institutional |
| 9 | **"MP" gold badge**: Looks like a gaming clan icon, not a government portal | Lacks institutional gravitas |
| 10 | **Generic role switcher**: Plain dropdown with "Switch Role" label | Doesn't communicate purpose to MPLADS evaluators |
| 11 | **Card border fatigue**: Every element wrapped in rounded-xl border shadow-sm | Visual noise; no clear hierarchy |

---

## 3. Recommended Dashboard Structure — Ministry View

The redesigned Ministry Dashboard follows a **5-section information architecture** aligned with PS 190942's three Ministry needs: national oversight, compliance monitoring, and trend awareness.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SECTION 1: NATIONAL KPI BAR                                                │
│ Total Works │ Sanctioned Capital │ Disbursed Capital │ Utilization Rate     │
├─────────────────────────────────────────────────────────────────────────────┤
│ SECTION 2: FOUR INDEPENDENT MODULE SUMMARY CARDS                           │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌────────────┐│
│ │ Cost Anomalies   │ │ Duplicate Works │ │ Fund Anomalies  │ │ Statutory  ││
│ │ 986 HIGH         │ │ 50,000 HIGH     │ │ 1,737 HIGH      │ │ Delays     ││
│ │ H:986 M:XX L:XX  │ │ H:50k R:XX L:XX │ │ H:1737 M:XX L:X │ │ 15,263 HIGH││
│ │ [View Details →] │ │ [View Details →]│ │ [View Details →] │ │ [View →]   ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│ SECTION 3: STATE PERFORMANCE TABLE                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ State │ Works │ Sanctioned │ Disbursed │ Util% │ Hi Cost│Hi Fund│Hi Del│ │
│ │ UP    │ 12345 │ ₹800 Cr    │ ₹300 Cr   │ 37.5% │   120  │  200  │ 2100 │ │
│ │ ...   │ ...   │ ...        │ ...       │ ...   │   ...  │  ...  │ ...  │ │
│ │                                         Sortable by any column          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────┬──────────────────────────────────────────┤
│ SECTION 4: FINANCIAL PACING     │ SECTION 5: ATTENTION REQUIRED QUEUE      │
│ Top 10 States:                  │ Works with HIGH severity in ≥1 model:    │
│ Sanctioned vs Disbursed         │ ┌──────────────────────────────────────┐ │
│ (Horizontal bar chart)          │ │ WRK-001 │ Cost:HIGH + Delay:HIGH    │ │
│                                  │ │ WRK-002 │ Fund:HIGH                 │ │
│                                  │ │ WRK-003 │ Cost:HIGH + Fund:HIGH     │ │
│                                  │ │ ...     │ [View Work Dossier →]     │ │
│                                  │ └──────────────────────────────────────┘ │
└──────────────────────────────────┴──────────────────────────────────────────┘
```

### Section 1: National KPI Bar

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Instant macro-financial context for Ministry oversight |
| **API Source** | `healthService.getHealth()` → `total_works`; `analyticsService.getDistrictSummaries()` → aggregate `total_sanctioned_amount` and `total_disbursed_amount` across all districts |
| **Frontend Processing** | Sum `total_sanctioned_amount` and `total_disbursed_amount` from all DistrictSummaryItem[]. Calculate utilization = `(totalDisbursed / totalSanctioned) * 100` |
| **User Sees** | 4 compact KPI segments: **Total Works** (98,825), **Sanctioned** (₹5,431 Cr), **Disbursed** (₹2,260 Cr), **Utilization** (41.6%) |
| **PS Support** | National-level oversight |

### Section 2: Four Independent Module Summary Cards

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | At-a-glance severity distribution for each independent analytical model |
| **API Source** | For HIGH counts: `analyticsService.getCostAnomalies({severity:'HIGH', page_size:1})` → `pagination.total_records`. Same pattern for all 4 models. For MEDIUM/LOW counts: same calls with severity MEDIUM and LOW |
| **Frontend Processing** | 4 parallel API calls per model × 3 severity levels = 12 calls (lightweight — page_size:1, only pagination metadata needed). Cache with TanStack Query's 5-min staleTime |
| **User Sees** | 4 compact cards, each showing: Model name, HIGH count (prominent), severity distribution bar (H/M/L), brief one-line methodology label, action link to full analytics page |
| **Interaction** | Click card → navigate to corresponding `/analytics/*` page |
| **PS Support** | Anomaly detection overview; risk-based alert surface |

> [!NOTE]
> Each card is compact (not the large "investigative triage panels" from the previous plan). They summarize; investigation happens on the dedicated analytics pages.

> [!IMPORTANT]
> The four models are NEVER combined into a composite score. Each card is independent. There is no "overall risk" indicator.

### Section 3: State Performance Table

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Geographic oversight at the state level — the primary administrative unit for Ministry monitoring |
| **API Source** | `analyticsService.getDistrictSummaries()` → returns all ~500 district records with `state` field |
| **Frontend Processing** | Group by `state`, aggregate: sum(total_works), sum(total_sanctioned_amount), sum(total_disbursed_amount), sum(high_cost_anomalies), sum(high_fund_anomalies), sum(high_delays). Calculate utilization per state. Sort by default: total_sanctioned_amount DESC |
| **User Sees** | Sortable table with columns: State, Total Works, Sanctioned (₹ Cr), Disbursed (₹ Cr), Utilization %, HIGH Cost Anomalies, HIGH Fund Anomalies, HIGH Delays |
| **Interaction** | Click column header → sort. Click state row → navigate to `/analytics/district-summary?state=X` |
| **PS Support** | National-level oversight; enables identification of underperforming states |

> [!IMPORTANT]
> There must NEVER be a blended "Risk" column. There must NEVER be a composite ranking. Each model's HIGH count is shown independently.

### Section 4: Financial Pacing Chart

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Visual answer to: "Which states have the largest gap between sanctioned capital and actual disbursement?" |
| **API Source** | Same state-aggregated data from Section 3 |
| **Frontend Processing** | Take top 10 states by total_sanctioned_amount, plot horizontal grouped bars |
| **User Sees** | Horizontal bar chart: Navy bars (Sanctioned) vs Amber bars (Disbursed) per state. Formatted tooltips with ₹ Cr values and utilization % |
| **PS Support** | Fund utilization monitoring; expenditure pattern visibility |

### Section 5: Attention Required Queue

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Surface individual works that have HIGH-severity findings, showing which model(s) flagged them |
| **API Source** | `analyticsService.getCostAnomalies({severity:'HIGH', page_size:5})`, `analyticsService.getFundAnomalies({severity:'HIGH', page_size:5})`, `analyticsService.getDelays({severity:'HIGH', page_size:5})` — each returns items with work_id |
| **Frontend Processing** | Collect work_ids from all 3 model responses. Merge by work_id to show which models flagged each work. Display up to ~10 unique works sorted by number of models flagging them |
| **User Sees** | List of work IDs, each with colored tags showing which model(s) flagged them (e.g., "Cost: HIGH", "Delay: HIGH"). Direct link to `/works/:workId` dossier |
| **Interaction** | Click work → navigate to full work dossier with all 4 model profiles |
| **PS Support** | Risk-based alerts; early warning; decision support for corrective action |

> [!NOTE]
> Duplicate Works (Model 2) are pair-grain, not work-grain, so they are excluded from this merge to avoid confusion. They remain accessible via the dedicated duplicate analytics page and work dossier.

---

## 4. Recommended Sidebar & Navigation Structure

### Current Sidebar Structure
```
OVERVIEW
  ├─ Executive Dashboard
  └─ Works Registry
INDEPENDENT AUDITS (4)  [collapsible]
  ├─ 1. Cost Anomalies
  ├─ 2. Potential Duplicates
  ├─ 3. Fund & Expenditure
  └─ 4. Statutory Delays
GOVERNANCE SUMMARIES
  ├─ District Performance
  └─ MP Portfolios
ADMINISTRATION  [Ministry only]
  └─ Stakeholder Accounts
```

### Recommended Sidebar Structure
```
MONITORING
  ├─ Dashboard                    (/dashboard)
  └─ Works Registry               (/works)

ANALYTICAL MODULES
  ├─ Cost Anomaly Detection        (/analytics/cost-anomalies)     [rose indicator]
  ├─ Duplicate Work Detection      (/analytics/duplicate-works)    [indigo indicator]
  ├─ Fund & Expenditure Audit      (/analytics/fund-anomalies)     [amber indicator]
  └─ Statutory Delay Tracking      (/analytics/delays)             [blue indicator]

GOVERNANCE
  ├─ District Performance          (/analytics/district-summary)
  └─ MP Portfolio Summary          (/analytics/mp-summary)

ADMINISTRATION  [Ministry only]
  └─ Stakeholder Accounts          (/admin/users)
```

### Changes Explained

| Change | Rationale |
| :--- | :--- |
| Rename "OVERVIEW" → "MONITORING" | Aligns with PS language: "monitoring and analytics platform" |
| Rename "INDEPENDENT AUDITS (4)" → "ANALYTICAL MODULES" | Cleaner; "(4)" count is redundant when you can see the 4 items |
| Remove collapsible toggle | All 4 modules should always be visible — they are core functionality |
| Rename items to match PS language | "Cost Anomaly Detection" instead of just "Cost Anomalies" |
| Keep section headings as uppercase labels | Maintains clean visual grouping |

### Visual Changes

| Element | Current | Proposed |
| :--- | :--- | :--- |
| Background | Jet black bg-slate-900 | Refined dark navy bg-[#0f172a] with softer contrast |
| Logo/badge | Gold "MP" squircle | Clean text wordmark: "MPLADS" with "AI Monitor" subtitle |
| Active state | Light background highlight | Left border accent (border-l-3 border-blue-500) + subtle bg tint |
| Model indicators | Color circles (rose, indigo, amber, blue) | Keep — works well for quick visual identification |
| Footer | "Team MPLADS Core Analytics Team" + "Zero Composite Risk" | Keep attribution; refine typography |

---

## 5. Header Improvements

### Current Header
- Left: Scope badge (role-specific jurisdiction label)
- Center: API health indicator (green/red dot)
- Right: "Switch Role" dropdown + user profile + logout

### Recommended Changes

| Element | Change | Rationale |
| :--- | :--- | :--- |
| Scope badge | Keep as-is — already well-designed per role | Works correctly |
| Health indicator | Keep; optionally show DB latency in ms on hover | Already functional |
| Role switcher label | Rename "Switch Role" → "Simulate Perspective" | Communicates purpose for MPLADS evaluators |
| Role switcher dropdown | Add jurisdiction scope text per role option | Evaluators see what each role can access |
| User profile | Keep; refine typography | Minor visual polish |

---

## 6. Key Visual/Hierarchy Changes (Cross-Cutting)

| # | Change | Files Affected | Nature |
| :--: | :--- | :--- | :--- |
| 1 | **Government color palette**: Deep navy primary, restrained blue interactive, amber/red/green severity | tailwind.config.js, index.css | Config |
| 2 | **Refined border radius**: rounded-lg (8px) instead of rounded-xl (16px) everywhere | All components | Visual |
| 3 | **Reduced card borders**: Use spacing and typography hierarchy instead of wrapping everything in bordered cards | MetricCard.tsx, Dashboard.tsx | Visual |
| 4 | **Tabular number formatting**: Use font-variant-numeric: tabular-nums for financial figures; format ₹ Cr consistently | index.css, dashboard components | Visual |
| 5 | **Severity colors standardized**: HIGH=rose/red, MEDIUM=amber, LOW=muted slate, compliant=emerald | Badge.tsx, all severity displays | Visual |
| 6 | **Login page institutional styling**: Light background, official scheme identity, compact demo account selector | Login.tsx | Redesign |

---

## 7. Existing APIs That Power the Redesign

**Zero backend changes required.** Every dashboard section is powered by existing endpoints:

| Dashboard Section | API Endpoint(s) | Key Fields Used |
| :--- | :--- | :--- |
| National KPI Bar | `GET /health` + `GET /analytics/district-summary` | total_works, total_sanctioned_amount, total_disbursed_amount |
| Module Summary Cards | `GET /analytics/cost-anomalies?severity=HIGH&page_size=1` (×3 severities ×4 models) | pagination.total_records |
| State Performance Table | `GET /analytics/district-summary` | All DistrictSummaryItem fields, grouped by state |
| Financial Pacing Chart | Same as State Performance (derived) | total_sanctioned_amount, total_disbursed_amount per state |
| Attention Queue | `GET /analytics/cost-anomalies?severity=HIGH&page_size=5` + fund-anomalies + delays (HIGH, page_size=5 each) | work_id from each, merged client-side |

---

## 8. What Must NOT Change

| Category | Specifics |
| :--- | :--- |
| **Backend code** | Zero changes to api/, database/, ml_models/, rule_engines/ |
| **API schemas** | Zero changes to Pydantic models or response structures |
| **Authentication & RBAC** | JWT in localStorage, Bearer injection, server-side jurisdictional scoping — all untouched |
| **Existing routes** | All 13 frontend routes remain intact and functional |
| **Analytics pages** | CostAnomalies, DuplicateWorks, FundAnomalies, StatutoryDelays — working; visual polish only |
| **Works Registry & Detail** | Fully functional; visual polish only |
| **Summary pages** | DistrictSummary, MPSummary — fully functional; visual polish only |
| **State/District/MP dashboards** | These role-specific sub-views are functional; minor visual alignment only |
| **4-model independence** | No composite score, no blended severity, no combined ranking |

---

## 9. PS 190942 Coverage Summary

### ✅ Fully Covered by Redesign
- Anomaly detection across 4 dimensions (cost, duplicates, fund, delays)
- Decision-support dashboards for all 4 stakeholder tiers
- Risk-based severity flagging with HIGH/MEDIUM/LOW per model
- State-level and district-level geographic oversight
- Fund utilization visibility (sanctioned vs disbursed)

### ⚠️ Partially Covered (Honest Labeling Required)
- **Compliance monitoring** → Label as "Statutory Delay Compliance" only
- **Trend analysis** → No time-series endpoint; if shown, label as "Historical Distribution"

### ❌ Not Implemented (Must NOT Simulate)
- Predictive insights / forecasting
- Proactive early warning / push notifications
- Broad compliance engine covering all MPLADS rules
- Composite risk scoring (intentionally excluded by design)

---

## 10. Files That Will Change

### Primary Changes (Structural)
| File | Change Type | Description |
| :--- | :--- | :--- |
| `frontend/src/pages/Dashboard.tsx` | **Major rewrite** | Replace MinistryDashboard with 5-section architecture |
| `frontend/src/components/layout/Sidebar.tsx` | **Moderate refactor** | Rename sections, remove collapsible, refine styling |
| `frontend/src/components/layout/Header.tsx` | **Minor refactor** | Rename role switcher, add jurisdiction descriptions |
| `frontend/src/pages/Login.tsx` | **Moderate redesign** | Light institutional theme, compact demo selector |

### Supporting Changes (Visual Polish)
| File | Change Type | Description |
| :--- | :--- | :--- |
| `frontend/tailwind.config.js` | Config update | Government color tokens |
| `frontend/src/index.css` | Style update | Tabular numbers, typography, utilities |
| `frontend/src/components/common/MetricCard.tsx` | Enhancement | Numeric formatting, severity display |
| `frontend/src/components/common/Badge.tsx` | Visual polish | Refined severity colors |
| `frontend/src/components/common/DataTable.tsx` | Visual polish | Tighter spacing, monospace numbers |

---

## 11. Implementation Order

| Step | Scope | Files |
| :--: | :--- | :--- |
| 1 | Design System Foundation: palette, typography | tailwind.config.js, index.css |
| 2 | Common Components Polish: Badge, MetricCard, DataTable | Badge.tsx, MetricCard.tsx, DataTable.tsx |
| 3 | Sidebar Restructure | Sidebar.tsx |
| 4 | Header Polish | Header.tsx |
| 5 | Login Page Redesign | Login.tsx |
| 6 | Ministry Dashboard Rewrite (5-section architecture) | Dashboard.tsx |
| 7 | Build Verification: `npm run build` must exit 0 | — |

---

## 12. Verification Plan

### Automated
- `npm run build` in frontend/ — must exit code 0, zero TypeScript errors

### Functional
- Login with all 4 demo accounts — verify role-appropriate dashboard renders
- All sidebar navigation links work
- All 4 module summary cards show real counts from API
- State Performance Table sorts correctly
- Attention Queue shows real HIGH-severity works
- Module cards navigate to correct /analytics/* pages
- State rows navigate to filtered district summary

### Integrity
- No composite risk score anywhere in UI
- No "Predictive", "Forecast", "AI Prediction" language
- No hardcoded/fake numbers — all from live API
- Backend pytest suite still passes (zero backend changes)

---

*End of Ministry Dashboard & Navigation UX Redesign Plan — v2.0*
