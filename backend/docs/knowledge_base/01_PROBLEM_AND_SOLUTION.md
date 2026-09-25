# 01. Problem Statement & Solution Overview

## Executive Overview & Real-World Context

The **Members of Parliament Local Area Development Scheme (MPLADS)** is a flagship Central Sector Scheme fully funded by the Government of India. Under this scheme, each Member of Parliament (MP) has the entitlement to recommend developmental works in their constituency costing up to **₹5 Crore per annum**, focusing primarily on creating durable community assets such as drinking water systems, primary health centers, rural roads, public libraries, school infrastructure, and sanitation facilities.

With **788 MPs** across both houses of Parliament (Lok Sabha and Rajya Sabha), over **₹3,900 Crore** is allocated annually for public assets across **36 States/UTs** and **773 Districts**. Across multiple parliamentary terms, this results in over **190,000 active and historical works** worth over **₹10,211 Crore**.

---

## The Core Governance Challenge

Monitoring government asset creation across 773 districts presents massive systemic hurdles:

1. **Massive Scale & Volume**: Manually reviewing 190,942 individual work recommendations, sanction orders, and 109,311 payment vouchers across 773 districts is physically impossible for human vigilance officers.
2. **Cost Overruns & Inflated Estimates**: Due to fragmented local tenders, sanction costs for identical works (e.g. *Installation of 50W Solar Street Light*) vary by 10x to 25x across adjacent districts or states without triggering red flags.
3. **Duplicate Work Sanctions & Double Billing**: Identical or overlapping physical projects (e.g., *Community Hall Construction*) are frequently sanctioned and billed multiple times under slightly altered names across consecutive years, adjacent boundaries, or different MPs.
4. **Financial Bottlenecks & Voucher Discrepancies**: Funds sit unutilized for years after sanction, or completed projects reflect 0 expenditure vouchers on portal records due to administrative reporting lag.
5. **Severe Statutory SLA Delays**: Over 51% of recommended works breach Para 3.12 of the official MPLADS Guidelines, which mandates that District Authorities accord sanction within **75 days** of receiving an MP recommendation.

---

## Pitch Versions for Stakeholders & Evaluators

### 1. One-Line Problem Statement
> *“Manual oversight fails at scale across 190,000+ distributed public works, enabling cost inflation, duplicate billing, dormant funds, and severe statutory SLA breaches.”*

### 2. 30-Second Elevator Pitch
> *“Under the MPLAD Scheme, MPs allocate ₹5 Crore annually for local infrastructure across 773 districts. Because monitoring nearly 200,000 works manually is impossible, millions of rupees are lost to inflated estimates, duplicate project billing, dormant allocations, and years of bureaucratic delay. We built the MPLADS AI Command Center — an end-to-end analytics platform powered by 4 independent ML and Rule engines that automatically audits every work for cost anomalies, semantic duplicates, fund irregularities, and statutory delay SLA breaches in real-time.”*

### 3. 2-Minute Presentation Pitch
> *“India’s MPLAD Scheme funds thousands of vital community assets every year. However, central and state authorities face a massive data dark-spot: 190,942 works worth over ₹10,200 Crore are recorded across fragmented portal dumps. Human vigilance teams cannot detect when a school hall in Bihar is sanctioned at 15 times the median state cost, or when two identical road repair projects are billed under different titles in the same district.*
>
> *Our solution, the MPLADS AI Command Center, transforms raw portal dumps into actionable governance intelligence. First, an automated ingestion scraper normalizes raw records into a canonical dataset. Next, four dedicated analytical engines evaluate each work independently:*
> *1. A Hierarchical Peer-Grouped Isolation Forest detects inflated cost estimates at sanction time with zero data leakage.*
> *2. A Transformer-based Sentence-BERT model combined with structural proximity signals detects duplicate work candidate pairs.*
> *3. A Multivariate Expenditure Isolation Forest flags voucher concentration anomalies and status-expenditure mismatches.*
> *4. A Statutory Rule Engine enforces the official 75-day sanction SLA and 365-day execution guidelines.*
>
> *Finally, an enterprise FastAPI gateway and React 18 command-center dashboard present role-scoped risk dossiers to Central Ministry, State, District, and MP stakeholders, complete with an AI assistant for natural-language inquiry.”*

### 4. Detailed Technical Problem Statement
> *“To design, implement, and validate an automated, scalable data-processing and machine-learning governance platform capable of ingesting heterogeneous administrative records of the MPLADS scheme, normalizing currency, date, and text fields into a canonical schema of 190,942 works, engineering domain-specific feature registries, executing four strictly independent anomaly and compliance models (Cost Anomaly Isolation Forest, Sentence-Transformer Duplicate Matcher, Expenditure Cohort Isolation Forest, and Statutory SLA Rule Engine), storing results in a cloud PostgreSQL database with strict Row Level Security, and exposing server-side RBAC-scoped REST APIs to a responsive React command-center interface.”*

---

## Exactly What WE Built — Solution Architecture

The **MPLADS AI Command Center** is an integrated governance analytics platform consisting of:

- **Live Data Scraper (`scraper/`)**: Automated crawler utilizing Scrapling and Async HTTP to ingest raw portal dumps, compute SHA-256 content hashes, track change logs, and log ingestion runs.
- **Canonical Feature Pipeline (`data_pipeline/`, `feature_engineering/`)**: Cleaners that standardize Indian currency (`₹`), ISO dates, and tab control characters, unifying 190,942 works and 109,311 vouchers.
- **4 Independent Analytical Core Engines**:
  - **Model 1: Cost Anomaly Detector (`ml_models/cost_anomaly/`)**: Peer-grouped Isolation Forest benchmarking cost estimates against state/national work medians.
  - **Model 2: Duplicate Work Detector (`ml_models/duplicate_work/`)**: `all-MiniLM-L6-v2` dense embeddings (384-d) combined with structural proximity scoring across a 90-day candidate blocking window.
  - **Model 3: Fund Anomaly Detector (`ml_models/fund_expenditure_anomaly/`)**: Isolation Forest on active spenders + Herfindahl-Hirschman Index (HHI) payment concentration + deterministic status mismatch rules.
  - **Phase 5: Delay Rule Engine (`rule_engines/delay/`)**: Statutory SLA rule engine enforcing 75-day sanction limits and 365-day work completion windows against a fixed reference date (`2026-09-05`).
- **Supabase PostgreSQL 17.6 Relational Core (`database/`)**: Cloud database enforcing zero orphaned foreign keys and Row Level Security.
- **FastAPI Application Gateway (`api/`)**: OAuth2 Bearer JWT authentication, Bcrypt 12-round hashing with constant-time dummy timing attack mitigation, and server-side SQL predicate injection for 4 governance tiers (`MINISTRY`, `STATE_OFFICER`, `DISTRICT_OFFICER`, `MP`).
- **React 18 Command Center SPA (`frontend/`)**: Vite, TypeScript, Tailwind CSS, Recharts, interactive district/MP summaries, work dossiers, and Subho AI chatbot powered by Groq LLM candidate fallback chains.

---

## Feature-by-Feature Micro Breakdown

| Feature | WHAT? | WHY? | HOW? | INPUT | PROCESS | OUTPUT | WHO USES IT? |
|---|---|---|---|---|---|---|---|
| **Cost Anomaly Audit** | Detects inflated cost estimates. | Prevents tender price padding. | Peer Isolation Forest. | Sanction amount, work type, state. | Hierarchical median IQR & Isolation Forest score. | Calibrated Score `[0,1]`, Severity (`HIGH/MED/LOW`). | District Officers & Ministry. |
| **Duplicate Work Matcher** | Flags double-billed projects. | Stops double funding. | Sentence-BERT + Structural scoring. | Work description, date, amount, location. | Candidate blocking (90d) + MiniLM-L6-v2 cosine similarity. | Candidate pairs with similarity score & reasons. | Vigilance Officers & State Nodal Authorities. |
| **Fund Anomaly Monitor** | Identifies payment irregularities. | Prevents voucher fraud & dormant funds. | Cohort Isolation Forest & HHI. | Voucher amounts, dates, work status. | Active spend HHI calculation & Status mismatch check. | Audit category, HHI score, anomaly reasons. | Ministry & District Planning Officers. |
| **Statutory Delay Tracker** | Measures SLA compliance. | Enforces legal timelines. | Rule Engine (Para 3.12). | Recommendation, sanction, completion dates. | SLA difference vs 75d & 365d limits against `2026-09-05`. | Delay score, primary delay type, overdue days. | MPs & State Officers. |
| **Subho AI Chatbot** | Conversational query interface. | Instant natural-language insights. | Groq LLM API + Context injection. | User prompt + scoped DB metrics. | Prompt injection filter + Role system prompt + Groq LLM fallback chain. | Natural language response with suggestions. | All Stakeholder Roles. |

