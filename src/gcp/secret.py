import logging

from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.cloud import secretmanager

from configuration.env import settings
from error.custom_exceptions import InternalAPIException
from service.logger import CustomLoggerAdapter

logger = CustomLoggerAdapter(logging.getLogger(__name__), None)


class SecretManager:
    def __init__(self) -> None:
        self._client = secretmanager.SecretManagerServiceClient()

    def get_secret(self, secret_id, version="latest"):
        logger.info(f"Retrieving secret {secret_id}")
        name = self._client.secret_version_path(
            settings.gcp_project_id, secret_id, version
        )

        try:
            response = self._client.access_secret_version(request={"name": name})
        except (GoogleAPICallError, RetryError, ValueError) as secret_mgr_error:
            error_str = f"Error Fetching Secret: {str(secret_mgr_error)}"
            logger.error(error_str)
            raise InternalAPIException(error_str) from secret_mgr_error

        try:
            payload = response.payload.data.decode("UTF-8")
        except UnicodeDecodeError as decode_error:
            error_str = f"Error Decoding Secret: {str(decode_error)}"
            logger.error(error_str)
            raise InternalAPIException(error_str) from decode_error

        return payload
