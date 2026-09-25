# 18. Technology Selection Justifications

## Technology Selection Justification Matrix

| Technology Selected | Alternative Considered | Why We Chose Selected | Why Alternative Was Rejected |
|---|---|---|---|
| **FastAPI** | Django / Flask | High performance async ASGI, automatic OpenAPI docs, strict Pydantic schema validation. | Django is overly heavy for REST API; Flask lacks native async and Pydantic integration. |
| **Supabase PostgreSQL** | MongoDB | Strict relational schema, foreign key constraints (0 orphan enforcement), native SQL joins. | MongoDB lacks ACID joins needed across works and expenditure tables. |
| **Isolation Forest** | Random Forest / XGBoost | Unsupervised anomaly detection; does not require historical labeled fraud data. | Supervised models require labeled fraud datasets which do not exist in government dumps. |
| **Sentence-BERT (`all-MiniLM-L6-v2`)** | TF-IDF / Cosine | Captures semantic context in work descriptions (e.g. *Water Tank* vs *Storage Reservoir*). | TF-IDF relies on exact word matches and misses semantic duplicates. |
| **Rule Engine (Delay)** | Machine Learning | Statutory SLAs (75d / 365d) are codified legal rules requiring 100% deterministic evaluation. | ML adds unnecessary probability/uncertainty to codified legal timelines. |
| **Bcrypt (12 rounds)** | Plain SHA-256 | Slow password hashing resistant to GPU brute-force attacks. | SHA-256 is too fast, enabling fast offline dictionary attacks. |

