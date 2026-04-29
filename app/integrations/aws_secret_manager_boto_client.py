import boto3
import logging
import time
import json


class AwsSecretManagerViaBotoApi:
    """AWS Secret Manager fetched using Boto Extension."""

    config_name = None
    TIMEOUT_IN_SECONDS = 10
    RETRY_ATTEMPTS = 2
    RETY_DELAY_IN_SECONDS = 0.3

    def __init__(self, config_name, region_name, logger: logging.Logger):
        self.config_name = config_name
        self.region_name = region_name
        self.client = boto3.client("secretsmanager", region_name=region_name)
        self.logger = logger

    def get_secrets(self):
        try:
            response = self.client.get_secret_value(SecretId=self.config_name)
            if "SecretString" in response:
                data = json.loads(response["SecretString"])
            else:
                data = response["SecretBinary"]

            is_success = True
        except Exception as e:
            self.logger.error(f"Error retrieving secret: {e}")
            is_success = False
            data = None

        return {"is_success": is_success, "data": data}

    def get_secrets_with_retry(self) -> dict:
        secret_result = {"is_success": False, "data": {}}

        for attempt in range(1, self.RETRY_ATTEMPTS):
            secret_result = self.get_secrets()
            if secret_result.get("is_success"):
                return secret_result

            self.logger.error(f"Failed request attempt #{attempt} for fetching secrets.")
            time.sleep(self.RETY_DELAY_IN_SECONDS)

        return secret_result
