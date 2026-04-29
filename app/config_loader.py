import os
import logging
from dotenv import load_dotenv

from integrations.aws_secret_manager_client import AwsSecretManagerViaLambdaExtensionApi
from integrations.aws_secret_manager_boto_client import AwsSecretManagerViaBotoApi

config_logger = logging.getLogger("config_logger")
config_logger.setLevel(logging.DEBUG)


def get_secret_settings():
    """Retrieves secret config from lambda extension / boto3."""
    secret_name = os.getenv("CONFIG_NAME")

    # Retrieve secret manager from lambda layer
    secret_layer_url = "http://localhost:" + str(
        os.getenv("PARAMETERS_SECRETS_EXTENSION_HTTP_PORT", "2773")
    )
    aws_secret_api = AwsSecretManagerViaLambdaExtensionApi(
        secret_name, secret_layer_url, logger=config_logger
    )
    secret_response = aws_secret_api.get_secrets_with_retry(
        query_params={"secretId": secret_name},
        api_token=os.environ.get("AWS_SESSION_TOKEN"),
    )

    if secret_response["is_success"]:
        config_logger.info("Successfully fetched secret settings from Lambda Layer.")
        return secret_response.get("data")

    # Retrieve secret manager using boto3
    aws_secret_api = AwsSecretManagerViaBotoApi(
        secret_name, region_name=os.getenv("REGION_NAME"), logger=config_logger
    )
    secret_response = aws_secret_api.get_secrets_with_retry()
    if secret_response["is_success"]:
        config_logger.info("Successfully fetched secret settings using Boto Client.")
        return secret_response.get("data")

    config_logger.error("Failed to fetch secret settings.")
    return {}


def load_secrets_to_env():
    """Loads settings from Secret Manager as new Env settings."""
    secrets = get_secret_settings()
    if not secrets or not isinstance(secrets, dict):
        return

    for key, value in secrets.items():
        os.environ[key] = value


def load_and_initialize_app_envs():
    """Load all related envs whether from .env or secrets
    depending on the situation.
    """
    if not os.getenv("ENV") or os.getenv("ENV") == "local":
        config_logger.info("Load .env settings")
        load_dotenv()
    else:
        config_logger.info("Load secret settings")
        load_secrets_to_env()


load_and_initialize_app_envs()
print("load env")
