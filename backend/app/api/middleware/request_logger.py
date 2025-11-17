"""
Request logging middleware.
Logs all incoming requests with timing information.
"""
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and log details."""

        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Extract request details
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        # Log incoming request
        logger.info(
            f"{method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_host": client_host,
                "event": "request_started",
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"{method} {path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_seconds": round(duration, 3),
                    "event": "request_completed",
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"{method} {path} - Error: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_seconds": round(duration, 3),
                    "error": str(exc),
                    "event": "request_failed",
                },
                exc_info=True
            )
            raise
