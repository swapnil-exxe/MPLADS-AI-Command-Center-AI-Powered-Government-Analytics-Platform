# 19. Hackathon & Evaluator Q&A

## Evaluator & Hackathon Judge Q&A

### Q1: What makes this project innovative compared to a standard government dashboard?
> *"Traditional dashboards only display static totals. The MPLADS AI Command Center actively detects risk: it benchmarks cost estimates against peer medians, matches duplicate work candidates using semantic NLP, flags voucher concentration anomalies, and enforces statutory legal deadlines with automated explainability."*

### Q2: How does the system handle false positives in Duplicate Work Detection?
> *"In municipal governance, legitimate phased works (e.g. Road Phase 1 and Road Phase 2) share similar language. Our duplicate matcher flags candidate pairs for human review rather than automatically deleting records. Vigilance officers receive ranked audit queues with detailed explanation vectors."*

### Q3: How scalable is the architecture?
> *"The backend is stateless and horizontally scalable via FastAPI/Uvicorn. PostgreSQL queries are optimized with composite B-Tree indexes. Dense embeddings are pre-cached, and candidate blocking windows reduce duplicate comparisons by 99.95%."*

