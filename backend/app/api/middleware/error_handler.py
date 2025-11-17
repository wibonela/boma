"""
Global error handling middleware.
Catches and handles all unhandled exceptions.
"""
from typing import Callable
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle unhandled exceptions globally."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and handle any exceptions."""

        try:
            return await call_next(request)

        except ValueError as exc:
            # Handle validation errors
            logger.warning(
                f"Validation error: {str(exc)}",
                extra={
                    "error_type": "validation_error",
                    "path": request.url.path,
                }
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation Error",
                    "detail": str(exc),
                    "type": "validation_error",
                }
            )

        except PermissionError as exc:
            # Handle permission errors
            logger.warning(
                f"Permission denied: {str(exc)}",
                extra={
                    "error_type": "permission_error",
                    "path": request.url.path,
                }
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Permission Denied",
                    "detail": str(exc),
                    "type": "permission_error",
                }
            )

        except Exception as exc:
            # Handle all other unhandled exceptions
            request_id = getattr(request.state, "request_id", "unknown")

            logger.error(
                f"Unhandled exception: {str(exc)}",
                extra={
                    "error_type": type(exc).__name__,
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                },
                exc_info=True
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id,
                    "type": "internal_error",
                }
            )
