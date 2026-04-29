import requests
import logging

from utilities.request_util import HttpRequestorInterface, HttpRequestorResponse


class HttpJsonRequestor(HttpRequestorInterface):
    """Uses python requests package as HTTP Request Client with JSON Content Type."""

    base_url = None
    headers = {}
    DEFAULT_CONTENT_TYPE = "application/json"
    DEFAULT_TIMEOUT_IN_SECONDS = 20
    GET_METHOD = "get"
    POST_METHOD = "post"
    PUT_METHOD = "put"
    DELETE_METHOD = "delete"
    PATCH_METHOD = "patch"

    def __init__(self, base_url, logger: logging.Logger):
        self.base_url = base_url
        self.logger = logger
        self.headers = {}
        self.set_header("Content-Type", self.DEFAULT_CONTENT_TYPE)

    def get_headers(self) -> dict:
        return self.headers

    def set_header(self, key, value):
        self.headers[key] = value

    def send_request(
        self,
        method,
        url,
        query_params=None,
        body_params=None,
        headers=None,
        timeout=None,
    ) -> HttpRequestorResponse:
        action_log = f"Send {str(method).upper()} request to {url}"
        print(action_log)

        try:
            request_params = {
                "headers": headers,
                "params": query_params if isinstance(query_params, dict) else {},
                "json": body_params if isinstance(body_params, dict) else {},
                "timeout": timeout if not timeout else self.DEFAULT_TIMEOUT_IN_SECONDS,
            }
            if method == self.GET_METHOD:
                response = requests.get(url, **request_params)
            elif method == self.POST_METHOD:
                response = requests.post(url, **request_params)
            elif method == self.PATCH_METHOD:
                response = requests.patch(url, **request_params)
            elif method == self.DELETE_METHOD:
                response = requests.delete(url, **request_params)
            else:
                raise ValueError("Invalid http request method.")

            try:
                content = response.json()
            except Exception as e:
                response_text = response.text
                self.logger.error(
                    f"{action_log}. Failed to parse json response error: {e}. Response: {response_text}"
                )
                content = {"content": response_text}

            result = HttpRequestorResponse(
                content=content,
                raw_response=response,
                status_code=response.status_code,
                is_ok=response.ok,
            )
            response_duration = response.elapsed.total_seconds()
            self.logger.info(
                f"{action_log} || Response Duration: {response_duration}s"
                f" || Status: {response.status_code}"
            )
        except Exception as e:
            self.logger.error(f"{action_log}. Failed to get expected response. {e}")
            result = HttpRequestorResponse(
                response={}, is_ok=False, status_code=0, content=None, raw_response=None
            )

        return result

    def get(self, api_endpoint, query_params=None, body_params=None, timeout=None) -> HttpRequestorResponse:
        headers = self.get_headers()
        request_url = f"{self.base_url}{api_endpoint}"
        return self.send_request(self.GET_METHOD, request_url, headers=headers, query_params=query_params, body_params=body_params, timeout=timeout)

    def post(self, api_endpoint, query_params=None, body_params=None, timeout=None) -> HttpRequestorResponse:
        headers = self.get_headers()
        request_url = f"{self.base_url}{api_endpoint}"
        return self.send_request(self.POST_METHOD, request_url, headers=headers, query_params=query_params, body_params=body_params, timeout=timeout)

    def patch(self, api_endpoint, query_params=None, body_params=None, timeout=None) -> HttpRequestorResponse:
        headers = self.get_headers()
        request_url = f"{self.base_url}{api_endpoint}"
        return self.send_request(self.PATCH_METHOD, request_url, headers=headers, query_params=query_params, body_params=body_params, timeout=timeout)

    def delete(self, api_endpoint, query_params=None, body_params=None, timeout=None) -> HttpRequestorResponse:
        headers = self.get_headers()
        request_url = f"{self.base_url}{api_endpoint}"
        return self.send_request(self.DELETE_METHOD, request_url, headers=headers, query_params=query_params, body_params=body_params, timeout=timeout)
