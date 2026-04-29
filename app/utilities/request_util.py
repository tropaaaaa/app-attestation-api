from pydantic import BaseModel
from typing import Optional, Any
from abc import ABC, abstractmethod


class HttpRequestorResponse(BaseModel):
    """HTTP Requestor Response Model."""

    status_code: int
    is_ok: bool
    content: Optional[dict] = None
    raw_response: Any

    class Config:
        arbitrary_types_allowed = True


class HttpRequestorInterface(ABC):
    """HTTP Requestor Interface."""

    @abstractmethod
    def get_headers(self) -> dict:
        """Retrieves headers to be used to the request."""

    @abstractmethod
    def set_header(self, key, value):
        """Sets specific header value to be used to the request."""

    @abstractmethod
    def get(self, api_endpoint, query_params, body_params) -> HttpRequestorResponse:
        """Get request."""

    @abstractmethod
    def post(self, api_endpoint, query_params, body_params) -> HttpRequestorResponse:
        """Post request."""

    @abstractmethod
    def patch(self, api_endpoint, query_params, body_params) -> HttpRequestorResponse:
        """Patch request."""

    @abstractmethod
    def delete(self, api_endpoint, query_params, body_params) -> HttpRequestorResponse:
        """Delete request."""
