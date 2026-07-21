"""
logging_middleware.py — HTTP request/response timing and audit middleware.

Attaches to the FastAPI application and logs every inbound request with:
  - HTTP method + path
  - Response status code
  - Wall-clock duration in milliseconds
  - A short correlation ID included in every log line for request tracing

The middleware is intentionally thin: it does NOT parse request bodies
(those are too expensive to buffer in middleware).  Detailed query-level
audit records (user_id, SQL, row_count) are emitted by audit_service
directly from the service layer, where all that context is available.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Header name the correlation ID is echoed back on (useful for debugging)
CORRELATION_HEADER = "X-Correlation-ID"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette/FastAPI middleware that:

      1. Generates a unique correlation ID for every request.
      2. Attaches it to the response as X-Correlation-ID.
      3. Logs method, path, status code, and duration on every response.

    Example log line:
        2024-01-01 12:00:00 | INFO | middleware | POST /api/v1/query
        → 200 | 142.3ms | corr=a1b2c3d4

    Usage:
        app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        logger.info(
            "→ %s %s | corr=%s",
            request.method,
            request.url.path,
            correlation_id,
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "✗ %s %s | ERROR | %.1fms | corr=%s",
                request.method,
                request.url.path,
                elapsed_ms,
                correlation_id,
                exc_info=exc,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers[CORRELATION_HEADER] = correlation_id

        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            "← %s %s | %d | %.1fms | corr=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            correlation_id,
        )

        return response
