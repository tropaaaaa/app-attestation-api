import json
import time
import logging
from abc import ABC, abstractmethod

from utilities.request_util import HttpRequestorInterface
from utilities.json_request_util import HttpJsonRequestor


class AwsSecretManagerApiInterface(ABC):
    """AWS Lambda Secret Manager API Interface."""

    @abstractmethod
    def set_api_token(self, token: str):
        """Sets API token used for request authentication."""

    @abstractmethod
    def get_secrets(self, query_params: dict, api_token: str) -> dict:
        """Retrieves secret manager values based on the config name."""

    @abstractmethod
    def get_secrets_with_retry(self, query_params: dict, api_token: str) -> dict:
        """Retrieves secret manager values with retries during failure."""


class AwsSecretManagerViaLambdaExtensionApi(AwsSecretManagerApiInterface):
    """AWS Secret Manager fetched using Lambda Layer Extension."""

    config_name = None
    base_url = None
    requestor = None
    TIMEOUT_IN_SECONDS = 10
    RETRY_ATTEMPTS = 3
    RETY_DELAY_IN_SECONDS = 0.3

    GET_SECRET_ENDPOINT = "/secretsmanager/get"

    def __init__(
        self,
        config_name,
        base_url,
        logger: logging.Logger,
        http_requestor: HttpRequestorInterface = HttpJsonRequestor,
    ):
        self.config_name = config_name
        self.base_url = base_url
        self.logger = logger
        self.requestor = http_requestor(base_url, logger=logger)

    def set_api_token(self, token):
        self.requestor.set_header("X-Aws-Parameters-Secrets-Token", token)

    def get_secrets(self, query_params: dict, api_token: str):
        endpoint = self.GET_SECRET_ENDPOINT

        self.logger.info(
            f"[AWS_SECRET] Get Secrets for {self.config_name}."
            f" Data: {json.dumps(query_params)}"
        )
        self.set_api_token(api_token)
        response = self.requestor.get(
            endpoint, query_params=query_params, timeout=self.TIMEOUT_IN_SECONDS
        )

        is_success = response.is_ok
        data = json.loads(response.content["SecretString"]) if is_success else {}

        return {"is_success": is_success, "data": data}

    def get_secrets_with_retry(self, query_params: dict, api_token: str) -> dict:
        secret_result = {"is_success": False, "data": {}}

        for attempt in range(1, self.RETRY_ATTEMPTS):
            secret_result = self.get_secrets(query_params=query_params, api_token=api_token)
            if secret_result.get("is_success"):
                return secret_result

            self.logger.error(f"Failed request attempt #{attempt} for fetching secrets.")
            time.sleep(self.RETY_DELAY_IN_SECONDS)

        return secret_result


class AwsSecretManagerBotoApiInterface(ABC):
    """AWS Lambda Secret Manager Boto API Interface."""

    @abstractmethod
    def set_api_token(self, token: str):
        """Sets API token used for request authentication."""

    @abstractmethod
    def get_secrets(self, query_params: dict, api_token: str) -> dict:
        """Retrieves secret manager values based on the config name."""

    @abstractmethod
    def get_secrets_with_retry(self, query_params: dict, api_token: str) -> dict:
        """Retrieves secret manager values with retries during failure."""
