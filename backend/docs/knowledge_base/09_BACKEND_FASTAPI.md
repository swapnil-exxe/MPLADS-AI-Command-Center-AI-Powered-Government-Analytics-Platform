# 09. FastAPI Backend Application Gateway

## FastAPI Application Gateway Architecture (`api/`)

The backend gateway acts as the secure intermediary between governance clients and database storage.

### Core Configuration

- **Framework**: FastAPI (`fastapi>=0.115.0`) on ASGI server Uvicorn.
- **Middleware**: CORS middleware, SlowAPI rate limiter (5 req/min on login), process-time diagnostic header (`X-Process-Time-Ms`).
- **SPA Routing**: Mounts `/videos` and `/assets`, serving `frontend/dist/index.html` for unknown client-side routes.

### Primary Endpoint Categories

- `/api/v1/health`: Connection check and latencies.
- `/api/v1/auth/*`: Authentication, token generation, user profiles, user provisioning.
- `/api/v1/works/*`: Work list catalog and single-work dossiers.
- `/api/v1/analytics/*`: Model-specific detections (cost anomalies, duplicate pairs, fund anomalies, delays, district/MP summaries).
- `/api/v1/chat/*`: Subho AI chatbot query endpoints.

