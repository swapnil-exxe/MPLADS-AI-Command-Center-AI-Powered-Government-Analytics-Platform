# 14. Performance Optimization & Deployment Guide

## Performance Optimization & Deployment Architecture

### Performance Optimizations
1. **Database Indexing**: B-Tree composite indexes on `(state, district)`, `(work_id_1, work_id_2)`, `work_status`, and `severity`.
2. **Columnar Parquet Processing**: Offline model scoring uses Apache Parquet for fast memory-mapped vectorized Pandas operations.
3. **Frontend Bundle Single-File SPA**: Production bundle compiled to `frontend/dist/index.html` (1,003 kB), served directly by FastAPI.

### Deployment Workflow
- **Localhost Backend**: FastAPI / Uvicorn hosted locally at `http://127.0.0.1:8000/api/v1` connected to Supabase PostgreSQL over SSL.
- **Environment Isolation**: `.env` file isolated on server; `.env.example` committed to repo.

