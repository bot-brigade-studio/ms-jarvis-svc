import httpx
import time
from typing import Optional, Dict
from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import APIError
from app.models.base import current_bearer_token


class BaseClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.logger = logger
        self.timeout = timeout
        self.bearer_token = current_bearer_token.get()
        self.default_headers = {"Authorization": f"Bearer {self.bearer_token}"}

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Generic method to handle all HTTP requests with common logic
        """
        time_start = time.time()
        url = f"{self.base_url}/{endpoint}"
        headers = {**self.default_headers, **kwargs.pop("headers", {})}

        self.logger.info(f"{method} request to {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method, url, data=data, json=json, headers=headers, **kwargs
                )

                if response.status_code >= 400:
                    raise APIError(
                        message=self._get_error_message(response),
                        status_code=response.status_code,
                    )

                self.logger.info(
                    f"Response: {response.status_code} in {time.time() - time_start:.2f} seconds"
                )
                return response

        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout in {method} request to {url}: {e}")
            raise APIError(message="Request timed out", status_code=504)

    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self._make_request("GET", endpoint, **kwargs)

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            "POST", endpoint, data=data, json=json, **kwargs
        )

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request("PUT", endpoint, data=data, json=json, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self._make_request("DELETE", endpoint, **kwargs)

    def _get_error_message(self, response: httpx.Response) -> str:
        """Extract error message from response"""
        if response.headers.get("content-type") == "application/json":
            json_response = response.json()
            return (
                json_response.get("detail")
                or json_response.get("message")
                or response.text
            )
        return response.text


class HeimdallClient(BaseClient):
    def __init__(self):
        super().__init__(settings.HEIMDALL_SERVICE_URL)


class SanctumClient(BaseClient):
    def __init__(self):
        super().__init__(settings.SANCTUM_SERVICE_URL)
