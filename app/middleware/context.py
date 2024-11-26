from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from app.models.base import current_user_id, current_tenant_id
from typing import Optional
from uuid import UUID
from app.core.logging import logger
from app.core.config import settings
import httpx



class ContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):  # Accept the app parameter
        super().__init__(app)  # Pass it to the superclass
        self.auth_service_url = settings.HEIMDALL_SERVICE_URL
        self.client = httpx.AsyncClient()
        
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Reset context di awal request
        token_user_id: Optional[UUID] = None
        token_tenant_id: Optional[UUID] = None
        
        try:
            if settings.ENVIRONMENT == "production" :
                if request.headers.get("X-User-ID"):
                    token_user_id = UUID(request.headers.get("X-User-ID"))
                if request.headers.get("X-Tenant-ID"):
                    token_tenant_id = UUID(request.headers.get("X-Tenant-ID"))
            else:
                token_auth = request.headers.get("Authorization")
                if token_auth:
                    token = token_auth.split(" ")[1]
                    response = await self.client.get(
                        f"{self.auth_service_url}/api/v1/rbac/validate-permission",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if response.status_code == 200:
                        token_user_id = UUID(response.json()["data"]["user_id"])
                        token_tenant_id = UUID(response.json()["data"]["tenant_id"])
                    else:
                        logger.error(f"Error in context middleware: {response.json()['message']}")
                
            # Set context variables
            if token_user_id:
                current_user_id.set(token_user_id)
            if token_tenant_id:
                current_tenant_id.set(token_tenant_id)
            
            # Process request
            response = await call_next(request)
            
            response.headers["X-User-ID"] = str(token_user_id)
            response.headers["X-Tenant-ID"] = str(token_tenant_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in context middleware: {str(e)}")
            raise
            
        finally:
            # Reset context di akhir request
            try:
                current_user_id.set(None)
                current_tenant_id.set(None)
            except Exception as e:
                logger.error(f"Error resetting context: {str(e)}")
                
                