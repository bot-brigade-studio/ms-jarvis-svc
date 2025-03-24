from typing import Optional
from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from app.models.base import (
    current_user_id,
    current_tenant_id,
    current_project_id,
)
from app.core.logging import logger

security = HTTPBearer(
    scheme_name="Bearer", description="Enter your Bearer token", auto_error=False
)


class CurrentUser(BaseModel):
    id: str
    tenant_id: str
    project_id: Optional[str] = None


# Dependency for w
async def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
) -> CurrentUser:
    """
    Get the current user from context variables.
    These values are set by the ContextMiddleware during request processing.
    """
    try:
        user_id = current_user_id.get()
        tenant_id = current_tenant_id.get()
        project_id = current_project_id.get()

        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication",
            )

        return CurrentUser(id=user_id, tenant_id=tenant_id, project_id=project_id)

    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
        )
