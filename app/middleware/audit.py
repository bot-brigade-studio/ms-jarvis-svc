from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
import time
import uuid

class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        start_time = time.time()
        
        # Extract request details
        request_details = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "headers": dict(request.headers),
        }

        # Log request
        logger.info(
            "Incoming request",
            extra={
                "event_type": "request_started",
                **request_details
            }
        )

        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "event_type": "request_completed",
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    **request_details
                }
            )
            
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "event_type": "request_failed",
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    **request_details
                }
            )
            raise