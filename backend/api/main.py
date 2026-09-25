import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.config import settings
from api.auth.limiter import limiter
from api.routers import (
    health_router,
    auth_router,
    works_router,
    cost_router,
    duplicate_router,
    fund_router,
    delay_router,
    summary_router,
    trend_router,
    chat_router,
    admin_scraper_router
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

def _custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    response = _rate_limit_exceeded_handler(request, exc)
    response.headers["Retry-After"] = "900"
    return response

# Attach slowapi rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _custom_rate_limit_exceeded_handler)


# CORS Middleware (Strict Origin Allowlist)
origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent"],
)

# Request Timing & Security Headers Middleware
@app.middleware("http")
async def add_security_headers_and_timing(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Register API v1 Routers (supports both /api/v1/... and root /... paths)
for router in [
    health_router, auth_router, works_router, cost_router, 
    duplicate_router, fund_router, delay_router, summary_router, 
    trend_router, chat_router, admin_scraper_router
]:
    app.include_router(router, prefix=settings.API_V1_STR)
    app.include_router(router)

# Serve Production Single-File React SPA Bundle
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException

dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if dist_dir.exists():
    if (dist_dir / "videos").exists():
        app.mount("/videos", StaticFiles(directory=dist_dir / "videos"), name="videos")
    if (dist_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Route not found")
        file_path = dist_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(dist_dir / "index.html")
else:
    @app.api_route("/", methods=["GET", "HEAD"], tags=["Root"])
    def root():
        return {
            "platform": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs_url": f"{settings.API_V1_STR}/docs",
            "health_check": f"{settings.API_V1_STR}/health"
        }
