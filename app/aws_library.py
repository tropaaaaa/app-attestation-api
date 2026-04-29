import boto3
import json
from botocore.exceptions import ClientError
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig


class AwsSecretManagerException(Exception):
    pass


class AwsSecretManager:
    name = None
    cache = None
    parameters = dict()

    def __init__(self, name, region_name, access_key_id=None, secret_access_key=None) -> None:
        self.session = boto3.session.Session()

        configuration = {"service_name": "secretsmanager", "region_name": region_name}
        if access_key_id and secret_access_key:
            configuration["aws_access_key_id"] = access_key_id
            configuration["aws_secret_access_key"] = secret_access_key

        client = self.session.client(**configuration)
        cache_config = SecretCacheConfig()

        self.name = name
        self.cache = SecretCache(config=cache_config, client=client)

    def set_name(self, name):
        self.name = name
        return self

    def load_secrets(self):
        try:
            secret_name = self.name
            print("Fetch AWS Secret Config: ", secret_name)
            config_values = self.cache.get_secret_string(secret_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                print("The requested secret " + secret_name + " was not found")
            elif e.response["Error"]["Code"] == "InvalidRequestException":
                print("The request was invalid due to:", e)
            elif e.response["Error"]["Code"] == "InvalidParameterException":
                print("The request had invalid params:", e)
            elif e.response["Error"]["Code"] == "DecryptionFailure":
                print("The requested secret can't be decrypted using the provided KMS key:", e)
            elif e.response["Error"]["Code"] == "InternalServiceError":
                print("An error occurred on service side:", e)
            raise AwsSecretManagerException(f"AWS Client Error: {e}")

        self.parameters = json.loads(config_values)
        return self

    def get_param(self, name, default=None):
        return self.parameters.get(name, default)

    def get_secrets(self):
        return self.parameters
