from typing import Optional, Tuple
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from app.core.exceptions import APIError
from app.models.base import (
    current_user_id,
    current_tenant_id,
    current_project_id,
    current_bearer_token,
)
from app.core.logging import logger
from app.utils.http_client import FuryClient

security = HTTPBearer(
    scheme_name="Bearer", description="Enter your Bearer token", auto_error=False
)


class CurrentUser(BaseModel):
    id: str
    tenant_id: str
    project_id: Optional[str] = None


async def _validate_permission(
    request: Request,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Validate bearer token and extract user/tenant IDs.
    Returns: Tuple of (user_id, tenant_id, project_id)
    """

    client = FuryClient()
    token = request.headers.get("Authorization", "")
    response = await client.get(
        f"api/v1/rbac/validate-permission",
        headers={
            "Authorization": token,
            "X-Original-URI": request.url.path,
            "X-Original-Method": request.method,
            "X-Original-Host": request.url.hostname,
            "X-Api-Key": request.headers.get("X-Api-Key", ""),
        },
    )

    if response.status_code != 200:
        logger.error(f"Token validation failed: {response.json().get('message')}")
        raise APIError(
            message=response.json().get("message"),
            status_code=response.status_code,
        )

    data = response.json().get("data", {})
    user_id = str(data["user_id"]) if data.get("user_id") else ""
    tenant_id = str(data["tenant_id"]) if data.get("tenant_id") else ""
    project_id = str(data["project_id"]) if data.get("project_id") else ""

    if not all([user_id, tenant_id, project_id]):
        raise APIError(message="Unauthorized", status_code=status.HTTP_401_UNAUTHORIZED)

    # Set context variables
    current_user_id.set(user_id)
    current_tenant_id.set(tenant_id)
    current_project_id.set(project_id)
    current_bearer_token.set(token)

    return user_id, tenant_id, project_id


async def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
) -> CurrentUser:
    """
    Validate permissions and set context variables for the current request.
    Returns: CurrentUser object with validated user information.
    """
    try:
        # Get and validate context
        user_id, tenant_id, project_id = await _validate_permission(request)

        return CurrentUser(id=user_id, tenant_id=tenant_id, project_id=project_id)

    except APIError as e:
        raise e

    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise APIError(message="Internal server error", status_code=500)
