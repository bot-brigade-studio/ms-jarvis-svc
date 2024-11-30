from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from app.core.exceptions import APIError
from app.models.base import current_user_id, current_tenant_id, current_bearer_token
from typing import Optional, Tuple
from app.core.logging import logger
from app.core.config import settings
import httpx


class ContextMiddleware(BaseHTTPMiddleware):
    """Middleware to handle user and tenant context for requests."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.auth_service_url = settings.HEIMDALL_SERVICE_URL
        self.client = httpx.AsyncClient()

    async def _validate_token(self, token: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Validate bearer token and extract user/tenant IDs.

        Returns:
            Tuple of (user_id, tenant_id)
        """
        try:
            response = await self.client.get(
                f"{self.auth_service_url}/api/v1/rbac/validate-permission",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code != 200:
                logger.error(
                    f"Token validation failed: {response.json().get('message')}"
                )
                return None, None

            data = response.json().get("data", {})
            user_id = str(data["user_id"]) if data.get("user_id") else None
            tenant_id = str(data["tenant_id"]) if data.get("tenant_id") else None

            return user_id, tenant_id

        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None, None

    async def _get_context_ids(
        self, request: Request
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract user and tenant IDs from request based on environment."""

        x_user_id = request.headers.get("X-User-ID")
        x_tenant_id = request.headers.get("X-Tenant-ID")

        if x_user_id and x_tenant_id:
            return str(x_user_id), str(x_tenant_id)

        # Non-production environment: validate bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None, None

        token = auth_header.split(" ")[1]
        current_bearer_token.set(token)
        return await self._validate_token(token)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and handle context management."""
        try:
            # Get context IDs
            user_id, tenant_id = await self._get_context_ids(request)

            # Set context variables
            current_user_id.set(user_id)
            current_tenant_id.set(tenant_id)

            # Process request
            response = await call_next(request)

            # Set response headers
            response.headers["X-User-ID"] = str(user_id) if user_id else ""
            response.headers["X-Tenant-ID"] = str(tenant_id) if tenant_id else ""

            return response

        except Exception as e:
            logger.error(f"Context middleware error: {str(e)}")
            raise APIError(message="Internal Server Error", status_code=500)

        finally:
            # Reset context
            self._reset_context()

    def _reset_context(self) -> None:
        """Reset all context variables."""
        try:
            current_user_id.set(None)
            current_tenant_id.set(None)
            current_bearer_token.set(None)
        except Exception as e:
            logger.error(f"Error resetting context: {str(e)}")
