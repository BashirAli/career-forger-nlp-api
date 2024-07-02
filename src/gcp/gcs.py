import io
import logging.config

from google.api_core.exceptions import GoogleAPIError
from google.cloud import storage
from google.cloud.exceptions import NotFound

from configuration.env import settings
from configuration.logger_config import logger_config
from error.custom_exceptions import ManualDLQError, PubsubReprocessError
from pydantic_model.api_model import ErrorEnum
from service.logger import CustomLoggerAdapter

logger = CustomLoggerAdapter(logging.getLogger(__name__), None)


class GoogleCloudStorage:
    """Class to interact with Google cloud storage"""

    def __init__(self, project_id):
        self._client = self._init_client(project_id)

    def _init_client(self, project_id):
        return storage.Client(project_id)

    def read_gcs_file_to_bytes(self, bucket_name, source_blob_name) -> bytes:
        """Reads a file as bytes from a gcs bucket.

        Arguments:
            bucket_name: Bucket name where the file resides
            source_blob_name: Name of the file to read

        Returns:
            bytes: The file as bytes

        """
        try:
            logger.info(msg=f"Reading file from the bucket: {bucket_name}")
            # Get the bucket
            bucket = self._client.bucket(bucket_name)
            # Get the blob (file) from the bucket
            blob = bucket.blob(source_blob_name)
            # Read the file content as bytes
            file_as_bytes = blob.download_as_bytes()
            logger.info(msg=f"Successfully read file from the bucket: {bucket_name}")

        except NotFound as e:
            error_value = f"Failed to read file from google cloud storage: {e}"
            logger.error(msg=error_value)
            raise ManualDLQError(
                original_request=logger_config.context.get().get("original_request"),
                error_desc=error_value,
                error_stage=ErrorEnum.FILE_NOT_FOUND,
            )

        except (GoogleAPIError, Exception) as e:
            error_value = f"Failed to read file from google cloud storage: {e}"
            logger.error(msg=error_value)
            raise PubsubReprocessError(
                original_request=logger_config.context.get().get("original_request"),
                error_desc=error_value,
                error_stage=ErrorEnum.GOOGLE_API_ERROR,
            )

        return file_as_bytes