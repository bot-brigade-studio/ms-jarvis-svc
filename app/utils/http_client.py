import httpx
import time
import uuid
from functools import lru_cache
from typing import Optional, Dict, ClassVar, Any, Callable, TypeVar, cast
from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import APIError
from app.models.base import (
    current_bearer_token,
    current_tenant_id,
    current_user_id,
    current_project_id,
)


# Circuit breaker states
class CircuitState:
    CLOSED = "CLOSED"  # Normal operation, requests flow through
    OPEN = "OPEN"  # Circuit is open, requests fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing if service is healthy again


class CircuitBreaker:
    """Implements the circuit breaker pattern to prevent cascading failures"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0

    def record_success(self) -> None:
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call"""
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

    def allow_request(self) -> bool:
        """Check if a request should be allowed based on circuit state"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        # In HALF_OPEN state, allow limited calls
        return self.half_open_calls < self.half_open_max_calls


# Type variable for the return type of the function
T = TypeVar("T")


# DNS cache to avoid repeated DNS lookups
@lru_cache(maxsize=100)
def get_dns_cache() -> Dict[str, Any]:
    """Get a shared DNS cache dictionary"""
    return {}


class BaseClient:
    # Shared clients across all instances
    _clients: ClassVar[Dict[str, httpx.AsyncClient]] = {}
    # Circuit breakers for each service
    _circuit_breakers: ClassVar[Dict[str, CircuitBreaker]] = {}
    # Default connection pool settings
    _default_limits = httpx.Limits(
        max_keepalive_connections=50,  # Increased from 20
        max_connections=200,  # Increased from 100
        keepalive_expiry=60.0,  # Keep connections alive for 60 seconds
    )

    def __init__(self, base_url: str, timeout: float = 10.0):  # Reduced default timeout
        self.base_url = base_url
        self.timeout = timeout

    @classmethod
    def get_circuit_breaker(cls, service_key: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a service"""
        if service_key not in cls._circuit_breakers:
            cls._circuit_breakers[service_key] = CircuitBreaker()
        return cls._circuit_breakers[service_key]

    @classmethod
    def get_client(cls, base_url: str, timeout: float) -> httpx.AsyncClient:
        """Get or create a shared HTTP client with connection pooling"""
        client_key = f"{base_url}:{timeout}"
        if client_key not in cls._clients:
            # Create client with optimized settings
            transport = httpx.AsyncHTTPTransport(
                limits=cls._default_limits,
                retries=1,  # Allow 1 retry for transient network issues
                http1=True,
                http2=False,  # Disable HTTP/2 for simplicity and performance
            )

            cls._clients[client_key] = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                transport=transport,
                follow_redirects=True,
                http2=False,  # Disable HTTP/2 for now for better performance
            )
        return cls._clients[client_key]

    async def with_circuit_breaker(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """Execute a function with circuit breaker protection"""
        service_key = self.base_url
        circuit_breaker = self.get_circuit_breaker(service_key)

        if not circuit_breaker.allow_request():
            logger.warning(f"Circuit breaker open for {service_key}, failing fast")
            raise APIError(message="Service temporarily unavailable", status_code=503)

        try:
            result = await func(*args, **kwargs)
            circuit_breaker.record_success()
            return cast(T, result)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadTimeout) as e:
            circuit_breaker.record_failure()
            logger.error(f"Request failed for {service_key}: {e}")
            raise APIError(message="Request failed", status_code=504)
        except Exception as e:
            # Only record failure for 5xx errors or network issues
            if isinstance(e, APIError) and e.status_code >= 500:
                circuit_breaker.record_failure()
            raise

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        raise_error: bool = False,
        **kwargs,
    ) -> httpx.Response:
        """
        Generic method to handle all HTTP requests with common logic
        """
        time_start = time.time()
        url = endpoint if endpoint.startswith("http") else endpoint

        # Baca context pada saat request
        self.bearer_token = current_bearer_token.get() or ""
        self.user_id = current_user_id.get() or ""
        self.tenant_id = current_tenant_id.get() or ""
        self.project_id = current_project_id.get() or ""

        self.default_headers = {
            "Authorization": self.bearer_token,
            "X-Tenant-Id": self.tenant_id,
            "X-User-Id": self.user_id,
            "X-Project-Id": self.project_id,
            "Connection": "keep-alive",
        }

        headers = {**self.default_headers, **kwargs.pop("headers", {})}

        req_id = str(uuid.uuid4())
        client = self.get_client(self.base_url, self.timeout)

        # Add detailed timing metrics
        connect_start = 0.0
        request_start = 0.0
        response_start = 0.0

        # Log request attempt
        logger.debug(
            f"Sending {method} request to {self.base_url}/{url}",
            extra={
                "event_type": "send_http_request",
                "http_request_id": req_id,
                "method": method,
                "url": f"{self.base_url}/{url}",
            },
        )

        async def execute_request():
            nonlocal connect_start, request_start, response_start
            connect_start = time.time()

            response = await client.request(
                method, url, data=data, json=json, headers=headers, **kwargs
            )

            response_start = time.time()
            return response

        try:
            # Execute request with circuit breaker protection
            response = await self.with_circuit_breaker(execute_request)

            # Calculate timing metrics
            duration_ms = round((time.time() - time_start) * 1000, 2)
            connect_time = (
                round((connect_start - time_start) * 1000, 2)
                if connect_start > 0
                else 0
            )
            response_time = (
                round((response_start - connect_start) * 1000, 2)
                if response_start > 0
                else 0
            )

            # Log detailed timing information
            logger.info(
                f"Received {method} response from {self.base_url}/{url} with status {response.status_code} in {duration_ms} ms",
                extra={
                    "event_type": "receive_http_response",
                    "http_request_id": req_id,
                    "method": method,
                    "url": f"{self.base_url}/{url}",
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "connect_time_ms": connect_time,
                    "response_time_ms": response_time,
                    "request_headers": headers,
                },
            )

            if response.status_code >= 400 and raise_error:
                raise APIError(
                    message=self._get_error_message(response),
                    status_code=response.status_code,
                )

            return response
        except httpx.TimeoutException as e:
            logger.error(f"Timeout in {method} request to {self.base_url}/{url}: {e}")
            raise APIError(message="Request timed out", status_code=504)
        except httpx.ConnectError as e:
            logger.error(
                f"Connection error in {method} request to {self.base_url}/{url}: {e}"
            )
            raise APIError(message="Connection error", status_code=503)

    async def get(
        self, endpoint: str, raise_error: bool = True, **kwargs
    ) -> httpx.Response:
        return await self._make_request(
            "GET", endpoint, raise_error=raise_error, **kwargs
        )

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        raise_error: bool = True,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            "POST", endpoint, data=data, json=json, raise_error=raise_error, **kwargs
        )

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        raise_error: bool = True,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            "PUT", endpoint, data=data, json=json, raise_error=raise_error, **kwargs
        )

    async def delete(
        self, endpoint: str, raise_error: bool = True, **kwargs
    ) -> httpx.Response:
        return await self._make_request(
            "DELETE", endpoint, raise_error=raise_error, **kwargs
        )

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


# Function to close all clients on application shutdown
async def close_http_clients():
    """Close all HTTP clients to free resources"""
    for client in BaseClient._clients.values():
        await client.aclose()
    BaseClient._clients.clear()


class HeimdallClient(BaseClient):
    def __init__(self):
        super().__init__(settings.HEIMDALL_SERVICE_URL)


class SanctumClient(BaseClient):
    def __init__(self):
        super().__init__(settings.SANCTUM_SERVICE_URL)


class NexusClient(BaseClient):
    def __init__(self):
        super().__init__(settings.NEXUS_SERVICE_URL)


class FrostClient(BaseClient):
    def __init__(self):
        super().__init__(settings.FROST_SERVICE_URL)


class FuryClient(BaseClient):
    """Client for Fury RBAC service with optimized settings"""

    def __init__(self):
        # Use a shorter timeout for RBAC service
        super().__init__(base_url=settings.FURY_SERVICE_URL, timeout=5.0)
