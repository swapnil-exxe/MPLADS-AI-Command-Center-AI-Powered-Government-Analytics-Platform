# Frontend UI/UX Redesign & Visual Improvement Plan
## AI-Powered MPLADS Monitoring & Decision-Support System
### MPLADS Analytics 2026 — Problem Statement PS 190942

**Document Version:** 1.0.0  
**Target Milestone:** Comprehensive Frontend Visual Polish & Decision-Support Re-architecture  
**Scope:** Client-side presentation layer (`frontend/src/`) only. Zero backend/API/database modifications.  

---

## 1. Current UI/UX Audit & Screenshots Analysis

Based on a thorough inspection of the running frontend and the three user-provided screenshots (`Login page`, `Ministry dashboard`, and `Role-switcher open`), the following architectural and visual issues have been cataloged:

### 1.1 Login Page (`media_1788962456761.png`)
* **Dark / SaaS Aesthetic**: Uses a heavy `bg-slate-900` dark background with a bright yellow "MP" squircle icon. It looks like a consumer crypto/fintech SaaS product or a startup landing page rather than an official Ministry portal (MoSPI / Government of India).
* **Oversized & Cramped Floating Box**: The login card floats in the center of an empty dark screen. Despite its size, the content inside is crowded.
* **Competitor Demo Accounts Grid**: The 4 demo account cards occupy >45% of the card area with heavy borders, visually overpowering the primary email/password authentication inputs.
* **Lack of Institutional Gravitas**: Lacks official emblems, national colors, scheme mandate, or clear administrative identity.

### 1.2 Ministry Dashboard (`media_1788962456764.png`)
* **Severe Visual Hierarchy Flaws**:
  - The top row consists of 4 equally-weighted cards. Card 1 displays a number (`98,825`), while Cards 2, 3, and 4 display static text labels (`Requires Review`, `Semantic Pairs`, `75d SLA Compliance`). Text and numeric metrics are jarringly mixed.
  - Directly beneath this row is *another* set of 4 horizontal cards repeating the exact same four models with small right arrows (`Model 1: Cost Anomalies ->`, etc.). This creates redundant, boxy clutter (8 cards for 4 models!).
* **Missing Executive Financial Context**: The dashboard fails to show the macro-financial picture: Total Sanctioned Outlay (₹5,431 Cr) and Total Disbursed Capital (₹2,260 Cr), which are already calculated by the backend!
* **Misleading/Uninformative Analytical Metrics**: The cards do not display the real counts of high-severity findings (e.g., 986 High Cost Outliers, 1,737 High Fund Anomalies, 15,263 High Delay Breaches), despite the API returning these exact totals.
* **Ineffective Chart Presentation**:
  - The "Financial Outlay by Sample Districts" bar chart arbitrarily takes the first 7 districts from the list without strategic ordering. The bars are spaced awkwardly with large gaps and lack formatted tooltips.
  - It does not answer an executive monitoring question such as *"Which districts have the lowest fund utilization despite high capital sanctions?"*
* **Weak Monitoring Queue**:
  - The "Districts Ranked by HIGH Delay Violations" section uses generic blue pill tags for delay counts and small text. It feels like a static list rather than an actionable triage queue.

### 1.3 Role Switcher (`media_1788962456768.png`)
* **Generic Dropdown Styling**: Appears as an off-the-shelf white box with default hover effects and user icons.
* **Unclear Demonstrative Purpose**: It does not visually convey its purpose as an official **"Stakeholder Perspective Simulation"** for MPLADS evaluators.

### 1.4 Global Shell & Sidebar
* **Stark Contrast & Heavy Darkness**: The sidebar is jet black (`bg-slate-900`) while the main content area is bright white (`bg-slate-50`). This stark dichotomy looks unintegrated.
* **Emblem / Logo**: The rounded golden "MP" badge looks like a gaming clan logo or generic media player icon rather than an official state emblem or MoSPI audit identity.
* **Excessive Borders & Cards**: Almost every element is wrapped in a `rounded-xl border border-slate-200 shadow-sm` container, creating "card fatigue."

---

## 2. Problems Identified (Categorized)

| # | Category | Specific Problem in Current Codebase | Impact on Evaluation |
| :-: | :--- | :--- | :--- |
| **1** | **Visual Hierarchy** | Flat visual plane; KPI numbers compete with static text labels; double-row of 8 redundant cards. | Evaluator cannot discern what is normal vs. what requires urgent audit intervention. |
| **2** | **Information Density** | Wasted vertical whitespace; missing macro-budget metrics (sanctioned outlay, disbursed funds, utilization %). | Dashboard feels empty and decorative rather than an intelligence decision-support platform. |
| **3** | **Card & Border Fatigue** | Ubiquitous use of cards, outlines, and borders (`rounded-xl border shadow-sm`) creates visual noise. | Lacks clean typographic separation and content grouping. |
| **4** | **Typography** | Inconsistent weights, non-tabular numbers in financial figures, absence of institutional sans-serif hierarchy. | Lacks the crisp, authoritative typography of modern government intelligence portals. |
| **5** | **Login Experience** | Dark-mode crypto/SaaS aesthetic; demo buttons visually overpower credentials form. | Fails to project an authentic Government of India administrative portal environment. |
| **6** | **Sidebar / Navigation** | Monolithic dark block with jarring contrast against light main pane; uninspired active states. | Navigation feels disconnected from the content surface. |
| **7** | **Chart Utility** | Bar chart shows random sample districts with large empty gaps; does not answer a decision question. | Evaluator perceives charts as decorative widgets rather than decision-support analytics. |
| **8** | **Actionable Triage** | Priority district list lacks interactive affordances and financial gravity. | Fails to communicate the operational flow: **MONITOR → IDENTIFY → INVESTIGATE → DECIDE**. |

---

## 3. Design Direction: Government Decision-Support System

The redesign adopts an **Authoritative, Modern Institutional Intelligence Aesthetic** (reminiscent of high-level government command centers, PM GatiShakti, and national audit platforms):

### 3.1 Visual Language & Palette
* **Backgrounds**: Light, crisp neutral canvas (`#f8fafc` slate-50). Clean white (`#ffffff`) content panels with sharp, subtle dividers (`#e2e8f0` slate-200). Zero dark-mode sprawl in the core workspace.
* **Primary Typography & Text**: Deep Navy / Charcoal (`#0f172a` slate-900) for primary headings; Neutral Slate (`#475569` slate-600) for supporting metadata.
* **Institutional Blue Accent**: Restrained Government Navy/Blue (`#1e3a8a` / `#1d4ed8`) for interactive triggers, primary buttons, and navigational anchors.
* **Statutory Severity Semantics**:
  - **High Severity / Urgent Breach**: Deep Crimson / Rose (`#b91c1c` / `#dc2626`) with soft tint backgrounds (`#fef2f2`).
  - **Medium / Attention Required**: Amber / Saffron (`#b45309` / `#d97706`) with soft tint (`#fffbeb`).
  - **Low / Compliant**: Muted Slate (`#475569`) or Subdued Emerald (`#15803d`).
  - **Data Exception**: Subtle Violet/Slate (`#6b21a8`).
* **Geometry & Surface Treatment**:
  - Moderate, refined border radius (`rounded-lg` 8px, eliminating childish 16px/24px bubbles).
  - 1px hairline borders (`border-slate-200 / border-slate-300`).
  - Subtle, elevation-based micro-shadows (`shadow-xs` / `shadow-sm`). Zero heavy drop-shadows or 3D effects.
  - Zero glassmorphism, zero neon glows, zero gratuitous animations.

---

## 4. Login Page Redesign

### 4.1 Concept: Official Government Portal Authentication Gateway
Transform the login screen into a credible **Ministry of Statistics and Programme Implementation (MoSPI)** administrative gateway:
1. **Official National Header**:
   - Government of India / MoSPI identity with official Ashoka emblem motif and bilingual title (*Ministry of Statistics & Programme Implementation*).
   - Scheme designation: *Members of Parliament Local Area Development Scheme (MPLADS)*.
2. **Dual-Zone Layout**:
   - **Left / Hero Context Panel (Desktop)**: Executive briefing on scheme mandate (98,825 works, ₹4,286+ Cr, 36 States/UTs, 4 independent analytical audit models, statutory 2023 SLA compliance).
   - **Right / Authentication Panel**: Compact, focused, white institutional login card:
     - Clear input labels with subtle icons (Email, Password).
     - Dignified institutional primary button: *"Sign In to Portal"* (Government Navy `#1e3a8a` with hover state).
     - **Secondary Evaluator Demo Switcher**: Relocated below the form as an elegant, clean segmented selector or subtle expandable card with micro-badges (`MINISTRY`, `STATE`, `DISTRICT`, `MP`). It remains 100% functional for 1-click login without visually hijacking the screen.
3. **Institutional Security Footer**:
   - Encrypted Session (RFC 7519 JWT), Bcrypt (12 rounds) timing attack defense, and server-side jurisdictional RBAC disclaimer.

---

## 5. Ministry Dashboard Redesign

The redesigned Ministry Dashboard will follow an explicit five-tier information architecture communicating **MONITOR → IDENTIFY → INVESTIGATE → DECIDE**:

```
+--------------------------------------------------------------------------------------------------------+
| 1. EXECUTIVE CONTEXT HEADER: National MPLADS Oversight | All-India (36 States/UTs) | Switch Perspective |
+--------------------------------------------------------------------------------------------------------+
| 2. NATIONAL MACRO PORTFOLIO KPI BANNER:                                                                |
|    Total Works (98,825) | Sanctioned Capital (₹5,431 Cr) | Disbursed (₹2,260 Cr) | Scheme Utilization (41.6%)   |
+--------------------------------------------------------------------------------------------------------+
| 3. FOUR INDEPENDENT ANALYTICAL AUDITS (Actionable Triage Cards - Zero Composite Score):                |
|    +--------------------+  +--------------------+  +--------------------+  +--------------------+      |
|    | MODEL 1: COST      |  | MODEL 2: DUPLICATE |  | MODEL 3: FUND      |  | MODEL 4: STATUTORY |      |
|    | ANOMALIES          |  | WORKS (REVIEW)     |  | ANOMALIES          |  | DELAY BREACHES     |      |
|    | 986 High Outliers  |  | 50,000 Potential   |  | 1,737 Disburs. Risk|  | 15,263 Overdue SLAs|      |
|    | Peer Group Z-Score |  | MiniLM Cosine NLP  |  | HHI Vendor & Dorm. |  | 75d Sanction SLA   |      |
|    | [Review Queue →]   |  | [Compare Pairs →]  |  | [Audit Funds →]    |  | [Enforce SLAs →]   |      |
|    +--------------------+  +--------------------+  +--------------------+  +--------------------+      |
+--------------------------------------------------------------------------------------------------------+
| 4. TWO-COLUMN DECISION SUPPORT WORKBENCH:                                                              |
|    +-----------------------------------------------+ +-----------------------------------------------+ |
|    | LEFT: National Budget Allocation vs Pacing    | | RIGHT: Priority District Triage Queue         | |
|    | (Top 7 States/Districts by Outlay vs Spend)   | | (Ranked by High Statutory Delay Violations)   | |
|    | Actionable Bar Chart with ₹ Cr Tooltips       | | Interactive Rows linking to District Dossiers | |
|    +-----------------------------------------------+ +-----------------------------------------------+ |
+--------------------------------------------------------------------------------------------------------+
```

### 5.1 Tier 1: Executive Context Header
- Displays national oversight badge with official Ashoka / Government building icon.
- Displays live API health telemetry (Pulse indicator + query round-trip latency).
- Houses the redesigned **"Stakeholder Perspective Simulation"** button.

### 5.2 Tier 2: National Macro Portfolio KPI Banner
- Replaces the generic top cards with a cohesive, unified 4-segment executive banner:
  1. **Total Master Works**: `98,825` (Database Catalog).
  2. **Total Sanctioned Outlay**: `₹5,431.23 Cr` (Aggregated from district summaries).
  3. **Cumulative Disbursed Funds**: `₹2,260.26 Cr` (Reconciled voucher transactions).
  4. **Scheme-Wide Financial Utilization**: `41.6%` (Progress bar + status).

### 5.3 Tier 3: Four Independent Analytical Audit Consoles (Zero Composite Score)
Instead of 8 redundant cards, create 4 distinct, high-impact **Investigative Triage Panels**, one for each decoupled model:
1. **Model 1: Cost Estimate Anomalies**:
   - Metric: `986 High-Severity Outliers`.
   - Subtext: *Works with estimates >300% above historical peer group median.*
   - Badge: `Isolation Forest | Peer Fallback`.
   - Action Link: *"Inspect 986 Cost Outliers →"*.
2. **Model 2: Potential Duplicate Proposals**:
   - Metric: `50,000 Flagged Pairs`.
   - Subtext: *Dense semantic text similarity & spatial-temporal overlap.*
   - Defensibility Notice: *Statistical candidates for human review (not confirmed fraud).*
   - Action Link: *"Review Candidate Pairs →"*.
3. **Model 3: Fund Pacing & Vendor Concentration**:
   - Metric: `1,737 High-Severity Findings`.
   - Subtext: *Dormant sanctions (>180d zero spend) and HHI payee concentration.*
   - Badge: `Vendor Risk & Disbursement`.
   - Action Link: *"Audit Financial Pacing →"*.
4. **Model 4: Statutory SLA Timeline Breaches**:
   - Metric: `15,263 SLA Violations`.
   - Subtext: *Para 3.12 breaches: >75 days recommendation-to-sanction.*
   - Badge: `MoSPI 2023 Guidelines`.
   - Action Link: *"Triage Overdue Works →"*.

### 5.4 Tier 4: Decision-Support Workbench (Charts & Priority Triage Queue)
- **Left Column — Financial Pacing Chart**:
  - Filter top 7 districts by sanctioned capital.
  - Dual bars: Sanctioned Outlay (`#1e3a8a` Government Navy) vs Disbursed Funds (`#d97706` Amber).
  - Clean Y-Axis with ₹ Crores, minimal gridlines, formatted hover tooltips.
  - Answers: *"Which high-capital districts are suffering from severe disbursement lag?"*
- **Right Column — Priority District Monitoring Queue**:
  - Ranked list of top districts sorted by `high_delays DESC`.
  - Displays Rank `#1` to `#5`, District Name, State Name, Outlay in ₹ Cr, and prominent High Delay badge.
  - Each item is clickable, navigating directly to `/analytics/district-summary?search={district}`.

---

## 6. Sidebar & Navigation Improvements

1. **Light / Unified Theme Alignment**:
   - Transition sidebar from jet black (`bg-slate-900`) to an elegant, high-contrast Slate Navy (`bg-[#0c1b2e]`) with subtle borders, or a clean white institutional navigation rail.
   - Clean Indian Ashoka / MoSPI emblem badge replacing the yellow "MP" icon.
2. **Improved Active States**:
   - High-contrast active tab indicator with subtle left border accent (`border-l-4 border-blue-600 bg-blue-50/10 text-white font-bold`).
3. **Clear Model Categorization**:
   - The *Independent Audits (4)* section styled as an official audit menu with color-coded bullet indicators:
     - Model 1: Rose (Cost)
     - Model 2: Indigo (Duplicates)
     - Model 3: Amber (Funds)
     - Model 4: Blue (Delays)
4. **Institutional Footer**:
   - Clean attribution: *MPLADS Analytics 2026 • Team MPLADS Core Analytics Team*.
   - Security verification: *Zero Composite Score • Server-Side RBAC Enforced*.

---

## 7. Role Switcher Improvements

1. **Official Contextual Nomenclature**:
   - Rename trigger from generic *"Switch Role"* to *"Simulate Stakeholder Perspective"*.
   - Replace standard dropdown with a structured administrative modal/popover.
2. **Clear Stakeholder Badges**:
   - Each role card clearly demarcates jurisdiction, constitutional tier, and bound territory:
     - **Central Ministry (MoSPI)**: National Scope (36 States/UTs, 98,825 works).
     - **State Nodal Officer**: State Scope (Uttar Pradesh, 75 districts).
     - **District Planning Officer**: District Scope (Patna, Bihar).
     - **Member of Parliament**: Personal Portfolio (Hon. Sarabjeet Singh Khalsa).
3. **Instant Visual Confirmation**:
   - Displays a checkmark and active highlight on the currently simulated role.

---

## 8. Component-Level System Refactor

| Component | Current Weakness | Redesign Specification | Nature of Change |
| :--- | :--- | :--- | :--- |
| **`Header.tsx`** | Loosely floating pills, generic status. | Institutional header bar with official emblem, jurisdiction badge, real-time latency ping, and simulation switcher. | Component Refactor |
| **`Sidebar.tsx`** | Stark black background, toy logo, basic active states. | Crisp institutional navigation rail with dignified branding, clear audit group, and active indicators. | Component Refactor |
| **`MetricCard.tsx`** | Boxy, colored border cards with mixed string/numeric values. | Unified KPI component supporting numeric values, trend subtotals, micro-badges, and statutory severity tags. | Component Refactor |
| **`Badge.tsx`** | Bubbly pill badges with high opacity. | Subtle, refined badges with hairline borders, uppercase tracking, and statutory severity colors. | Visual-only Refactor |
| **`DataTable.tsx`** | Generic table padding, basic pagination. | High-density administrative table with sticky headers, subtle zebra striping, monospace numeric alignment, and compact pagination controls. | Component Refactor |
| **`RateLimitBanner.tsx`** | Floating red box. | Top-pinned official alert banner with live countdown timer and SlowAPI compliance notice. | Visual-only Refactor |

---

## 9. Chart Improvements (Recharts)

1. **Remove Empty Space**:
   - Configure `margin={{ top: 10, right: 10, left: -15, bottom: 0 }}` in `BarChart`.
   - Set fixed `barSize={18}` to avoid monstrously wide bars when few districts are displayed.
2. **Meaningful Tooltips**:
   - Custom `GovernmentTooltip` component rendering formatted numbers:
     - Outlay: `₹XX.X Cr`
     - Disbursed: `₹XX.X Cr`
     - Utilization: `XX.X%`
3. **Color Discipline**:
   - Standardize Bar colors:
     - Sanctioned Outlay: Navy Blue (`#1e3a8a`).
     - Disbursed Capital: Saffron/Amber (`#d97706`).

---

## 10. Responsive Breakpoint Strategy

* **1440px+ (Large Desktop / Projectors / Juries)**: Full expanded 4-column KPI grid, 2-column decision workbench, comfortable 260px sidebar.
* **1280px (Standard Desktop)**: 4-column audit cards, 2-column charts, full-fidelity data tables.
* **1024px (Laptops / iPads Landscape)**: 2x2 grid for analytical audit cards, stacked charts, full-width monitoring queue.
* **768px (Tablets)**: Collapsible hamburger navigation rail, single-column stacked cards, horizontally scrollable data tables.

---

## 11. Exact Files & Components That Will Change

1. `frontend/src/index.css` (Base typography, custom scrollbars, institutional utility classes).
2. `frontend/tailwind.config.js` (Government color palette extensions: navy, slate, saffron, crimson).
3. `frontend/src/pages/Login.tsx` (Complete redesign into bilingual official MoSPI gateway).
4. `frontend/src/pages/Dashboard.tsx` (Complete redesign of `MinistryDashboard` with real data aggregation).
5. `frontend/src/components/layout/Header.tsx` (Refined jurisdiction badge, latency monitor, role switcher).
6. `frontend/src/components/layout/Sidebar.tsx` (Dignified styling, Ashoka/MoSPI motif, clean active states).
7. `frontend/src/components/common/MetricCard.tsx` (Enhanced typography, numeric formatting, subtle borders).
8. `frontend/src/components/common/Badge.tsx` (Refined statutory severity styling).
9. `frontend/src/components/common/DataTable.tsx` (High-density institutional styling, monospace numbers).

---

## 12. Existing APIs & Backend Data That Will Be Reused

**Zero backend changes. 100% powered by existing APIs:**
1. **`healthService.getHealth()`**:
   - Returns: `total_works` (`98,825`), `db_latency_ms`, `status` (`healthy`).
2. **`analyticsService.getDistrictSummaries()`**:
   - Returns: List of all 500+ districts with:
     - `total_works`, `total_sanctioned_amount`, `total_disbursed_amount`
     - `high_cost_anomalies`, `high_duplicate_pairs`, `high_fund_anomalies`, `high_delays`
   - Reused for: Macro budget totals, top priority district ranking, and outlay vs. disbursement bar chart.
3. **`analyticsService.getCostAnomalies({ severity: 'HIGH', page_size: 1 })`**:
   - Returns: `pagination.total_records` = **986**.
4. **`analyticsService.getDuplicateWorks({ severity: 'HIGH', page_size: 1 })`**:
   - Returns: `pagination.total_records` = **50,000**.
5. **`analyticsService.getFundAnomalies({ severity: 'HIGH', page_size: 1 })`**:
   - Returns: `pagination.total_records` = **1,737**.
6. **`analyticsService.getDelays({ severity: 'HIGH', page_size: 1 })`**:
   - Returns: `pagination.total_records` = **15,263**.
7. **`authService.login()` & `useAuth()`**:
   - 4 seeded canonical demo accounts from `database/seed_users.py`.

---

## 13. Explicit List of What Will NOT Be Changed

1. **NO Backend Code Modification**: Zero changes to `api/`, `database/`, `ml_models/`, `rule_engines/`, `data_pipeline/`.
2. **NO API Schema Changes**: Zero modifications to Pydantic models or request/response structures.
3. **NO Synthetic Composite Risk Scoring**: The four models remain completely independent.
4. **NO Invented / Hardcoded Numbers**: All dashboard values come directly from live API responses.
5. **NO Removal of Existing Routes**: `/dashboard`, `/works`, `/works/:id`, `/analytics/*`, `/admin/users` remain intact.
6. **NO Alteration of Authentication / RBAC**: JWT storage in `localStorage`, `Bearer` header injection, and server-side jurisdictional filtering remain untouched.

---

## 14. Classification of Proposed Changes

* **Visual-Only Changes**:
  - Color palette update (Government Navy, Slate, Crimson, Amber).
  - Hairstyle borders, subtle shadows, and typography hierarchy.
  - Login page layout transformation into an institutional split-panel portal.
  - Sidebar and Header visual polish.
* **Frontend Logic Changes (Using Existing API Data)**:
  - Aggregating total sanctioned outlay and disbursed capital from `analyticsService.getDistrictSummaries()`.
  - Fetching high-severity count metadata from `analyticsService.getCostAnomalies()`, `getDuplicateWorks()`, `getFundAnomalies()`, and `getDelays()`.
  - Sorting priority districts by `high_delays DESC` with financial outlay context.
* **Component Refactors**:
  - Upgrading `MetricCard.tsx`, `Badge.tsx`, `DataTable.tsx`, `Header.tsx`, and `Sidebar.tsx`.
* **Backend Modifications**:
  - **NOT IMPLEMENTED — BACKEND CHANGE PROHIBITED.**

---

## 15. Implementation Order

1. **Step 1: Foundational Design System (`tailwind.config.js` & `index.css`)**:
   - Configure government color tokens, institutional font settings, and utility classes.
2. **Step 2: Component Refinement (`Badge.tsx`, `MetricCard.tsx`, `DataTable.tsx`)**:
   - Ensure reusable components render with new hairline borders, crisp typography, and statutory colors.
3. **Step 3: Global Shell (`Sidebar.tsx`, `Header.tsx`, `AppLayout.tsx`)**:
   - Restyle navigation rail with dignified branding, active indicator, scope badges, and upgraded role switcher.
4. **Step 4: Login Page Redesign (`Login.tsx`)**:
   - Implement the institutional split-panel layout with official MoSPI identity and secondary evaluator demo switcher.
5. **Step 5: Ministry Dashboard Redesign (`Dashboard.tsx`)**:
   - Re-architect into the 4-tier decision-support structure: Macro Portfolio Banner $\rightarrow$ 4 Independent Audit Triage Panels $\rightarrow$ Decision Workbench (Chart + Priority Queue).
6. **Step 6: Build Verification & Regression Testing**:
   - Run `npm run build` in `frontend/` to confirm zero TypeScript errors.
   - Run integration tests via dev server proxy to confirm 100% functionality preservation.

---

## 16. Verification & Testing Plan

1. **Automated Build Test**:
   - Execute `npm run build` in `frontend/`. Must exit with code 0.
2. **Visual & Responsive Verification**:
   - Verify layout at 1440px, 1280px, 1024px, and 768px.
   - Check that no visual overlap, text clipping, or horizontal layout blowout occurs.
3. **Functional & Flow Verification**:
   - Test login with all 4 seeded accounts (`ministry@mplads.gov.in`, `state.up@mplads.gov.in`, `district.patna@mplads.gov.in`, `mp.khalsa@mplads.gov.in`).
   - Test "Simulate Stakeholder Perspective" dropdown in Header — ensure instant view switching.
   - Verify all links from the 4 audit triage panels navigate to their respective analytical consoles (`/analytics/*`).
   - Verify clicking priority districts navigates with proper search parameters.
4. **Zero Composite Score Check**:
   - Ensure no synthetic composite score formula is introduced in any component or calculation.

---
*End of Frontend UI/UX Redesign Plan — AI-Powered MPLADS Monitoring & Decision-Support System*
