# local_s3/api/deps.py
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.models.base import current_user_id, current_tenant_id
from app.core.logging import logger

security = HTTPBearer(
    scheme_name="Bearer", description="Enter your Bearer token", auto_error=True
)


class CurrentUser(BaseModel):
    id: UUID
    tenant_id: UUID


class AuthClient:
    def __init__(self):
        self.auth_service_url = settings.HEIMDALL_SERVICE_URL
        self.client = httpx.AsyncClient()

    async def validate_permission(self, token: str) -> CurrentUser:
        response = await self.client.get(
            f"{self.auth_service_url}/api/v1/rbac/validate-permission",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail=response.json()["message"]
            )

        response = response.json()
        return CurrentUser(
            id=response["data"]["user_id"], tenant_id=response["data"]["tenant_id"]
        )


# Dependency for routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_client: AuthClient = Depends(),
):
    try:
        user_id = current_user_id.get()
        tenant_id = current_tenant_id.get()
        if user_id and tenant_id:
            return CurrentUser(id=user_id, tenant_id=tenant_id)
        else:
            user_data = await auth_client.validate_permission(credentials.credentials)
            return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")
