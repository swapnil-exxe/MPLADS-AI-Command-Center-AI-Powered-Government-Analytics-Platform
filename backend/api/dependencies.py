from typing import Generator
from fastapi import Query
from sqlalchemy.orm import Session
from database.connection import get_session

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session lifecycle."""
    db = get_session()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass

class PaginationParams:
    """Dependency for validated pagination parameters."""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
