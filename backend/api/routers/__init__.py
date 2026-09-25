from api.routers.health import router as health_router
from api.routers.auth import router as auth_router
from api.routers.works import router as works_router
from api.routers.cost_anomalies import router as cost_router
from api.routers.duplicate_works import router as duplicate_router
from api.routers.fund_anomalies import router as fund_router
from api.routers.delays import router as delay_router
from api.routers.summaries import router as summary_router
from api.routers.trends import router as trend_router
from api.routers.chat import router as chat_router
from api.routers.admin_scraper import router as admin_scraper_router

__all__ = [
    "health_router", "auth_router", "works_router", "cost_router",
    "duplicate_router", "fund_router", "delay_router", "summary_router",
    "trend_router", "chat_router", "admin_scraper_router"
]

