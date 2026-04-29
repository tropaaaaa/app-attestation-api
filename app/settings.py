import os
from typing import Optional
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv

load_dotenv(override=False)


class SystemSettings(BaseModel):
    """Initial System Settings loaded from ENV."""

    ENV: str = None
    DEBUG_MODE: Optional[str] = "false"
    RELEASE_VERSION: str = "1.0.0"
    ALLOWED_HOST: str = "*"
    CONFIG_NAME: str = None
    PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL: Optional[str] = "info"
    PARAMETERS_SECRETS_EXTENSION_HTTP_PORT: Optional[str] = "2773"
    ENABLE_STR_LOG_MODE: str = "true"
    ENABLE_JSON_LOG_MODE: str = "false"
    X_API_KEY: str = ""
    LOCAL_AWS_CLIENT_ID: str = ""
    LOCAL_AWS_CLIENT_KEY: str = ""

    model_config = ConfigDict(
        env_prefix="", env_file=None, env_file_encoding="utf-8"
    )


class GoogleSettings(BaseModel):
    """Google Play Integrity API Settings."""

    # Android package name (e.g. com.example.myapp)
    ANDROID_PACKAGE_NAME: str = ""
    # Full service account JSON stored as a string (loaded from Secrets Manager or .env)
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""

    model_config = ConfigDict(
        env_prefix="", env_file=None, env_file_encoding="utf-8"
    )


class IosSettings(BaseModel):
    """iOS App Attestation Settings (future implementation)."""

    IOS_BUNDLE_ID: str = ""

    model_config = ConfigDict(
        env_prefix="", env_file=None, env_file_encoding="utf-8"
    )


# Access os.environ as a dictionary
env_dict = dict(os.environ)

system_settings = SystemSettings(**env_dict)
google_settings = GoogleSettings(**env_dict)
ios_settings = IosSettings(**env_dict)
