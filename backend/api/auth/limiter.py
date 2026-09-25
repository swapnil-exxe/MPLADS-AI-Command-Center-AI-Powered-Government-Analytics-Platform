import time
from collections import defaultdict
from typing import Dict, List
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import HTTPException, Request, status
from api.config import settings

# Slowapi general rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.RATE_LIMIT_STORAGE_URL,
    default_limits=["60/minute"]
)


class FailedLoginLimiter:
    """
    Tracks failed login attempts per client IP address.
    Enforces maximum 5 failed attempts per 15-minute window (900s).
    The 6th failed attempt returns HTTP 429 Too Many Requests with Retry-After.
    Successful logins reset the failure counter and are never counted as failures.
    """
    def __init__(self, max_failures: int = 5, window_seconds: int = 900):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        # Filter out failure timestamps older than window_seconds
        self._failures[client_ip] = [
            t for t in self._failures[client_ip] if now - t < self.window_seconds
        ]
        if len(self._failures[client_ip]) >= self.max_failures:
            oldest_attempt = self._failures[client_ip][0]
            retry_after = max(1, int(self.window_seconds - (now - oldest_attempt)))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please wait 15 minutes before trying again.",
                headers={"Retry-After": str(retry_after)}
            )

    def record_failure(self, request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        self._failures[client_ip].append(time.time())

    def record_success(self, request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        self._failures[client_ip].clear()

    def reset(self):
        """Reset all tracked IP failures (useful for testing)."""
        self._failures.clear()


failed_login_limiter = FailedLoginLimiter(max_failures=5, window_seconds=900)
