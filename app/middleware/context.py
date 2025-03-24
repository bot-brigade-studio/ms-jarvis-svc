from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from app.models.base import (
    current_user_id,
    current_tenant_id,
    current_bearer_token,
    current_project_id,
)
from typing import Optional, Tuple
from app.core.logging import logger

from app.utils.http_client import HeimdallClient


class ContextMiddleware(BaseHTTPMiddleware):
    """Middleware to handle user and tenant context for requests."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.client = HeimdallClient()

    async def _validate_token(
        self, request: Request, token: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Validate bearer token and extract user/tenant IDs.

        Returns:
            Tuple of (user_id, tenant_id, project_id)
        """
        # Early return if token is None or empty
        if not token:
            logger.warning("No token provided for validation")
            return None, None, None

        try:
            response = await self.client.get(
                f"api/v1/rbac/validate-permission",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Original-URI": request.url.path,
                    "X-Original-Method": request.method,
                    "X-Original-Host": request.url.hostname,
                    "X-Api-Key": request.headers.get("X-Api-Key", ""),
                },
            )

            if response.status_code != 200:
                logger.error(
                    f"Token validation failed: {response.json().get('message')}"
                )
                return None, None, None

            data = response.json().get("data", {})
            user_id = str(data["user_id"]) if data.get("user_id") else None
            tenant_id = str(data["tenant_id"]) if data.get("tenant_id") else None
            project_id = str(data["project_id"]) if data.get("project_id") else None

            return user_id, tenant_id, project_id

        except Exception as e:
            import traceback

            print(traceback.format_exc())
            logger.error(f"Token validation error: {str(e)}")
            return None, None, None

    async def _get_context_ids(
        self, request: Request
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract user and tenant IDs from request based on environment."""

        x_user_id = request.headers.get("X-User-ID")
        x_tenant_id = request.headers.get("X-Tenant-ID")
        x_project_id = request.headers.get("X-Project-ID")
        token = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            current_bearer_token.set(token)  # Set the bearer token here

        if x_user_id and x_tenant_id:
            return str(x_user_id), str(x_tenant_id), str(x_project_id)

        return await self._validate_token(request, token)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and handle context management."""
        try:
            # Get context IDs
            user_id, tenant_id, project_id = await self._get_context_ids(request)

            # Set context variables
            current_user_id.set(user_id)
            current_tenant_id.set(tenant_id)
            current_project_id.set(project_id)

            # Process request
            response = await call_next(request)

            # Set response headers
            response.headers["X-User-ID"] = str(user_id) if user_id else ""
            response.headers["X-Tenant-ID"] = str(tenant_id) if tenant_id else ""
            response.headers["X-Project-ID"] = str(project_id) if project_id else ""

            return response

        finally:
            self._reset_context()

    def _reset_context(self) -> None:
        """Reset all context variables."""
        try:
            current_user_id.set(None)
            current_tenant_id.set(None)
            current_bearer_token.set(None)
            current_project_id.set(None)
        except Exception as e:
            logger.error(f"Error resetting context: {str(e)}")
