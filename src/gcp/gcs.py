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

    def upload_stringio_to_gcs(self, target_bucket_name, target_blob_name, string_data):
        """Uploads string data to a gcs bucket.

        Arguments:
            target_bucket_name: Bucket name where the file should be uploaded
            target_blob_name: Name of the file to upload
            string_data: Data to upload

        """
        try:
            logger.info(msg=f"Uploading file to {target_bucket_name}")
            # Get the bucket
            bucket = self._client.bucket(target_bucket_name)
            # Create a new blob in the bucket
            blob = bucket.blob(target_blob_name)
            logger.info(msg=f"blob: {blob}")
            # Convert the StringIO object to a BytesIO object
            string_io = io.StringIO(string_data)
            bytes_io = io.BytesIO(string_io.getvalue().encode())
            # Upload the BytesIO object to the GCS bucket
            blob.upload_from_file(bytes_io, size=len(bytes_io.getvalue()))
            logger.info(msg=f"File uploaded to {target_bucket_name}")

        except NotFound as e:
            error_value = f"Failed to upload to GCS bucket: {e}"
            logger.error(msg=error_value)
            raise ManualDLQError(
                original_request=logger_config.context.get().get("original_request"),
                error_desc=error_value,
                error_stage=ErrorEnum.UPLOAD_TO_GCS,
            )
        except (GoogleAPIError, Exception) as e:
            error_value = f"Failed to upload to GCS bucket - {target_bucket_name}: {e}"
            logger.error(msg=error_value)
            logger.error(msg=logger_config.context.get().get("original_request"))

            raise PubsubReprocessError(
                original_request=logger_config.context.get().get("original_request"),
                error_desc=error_value,
                error_stage=ErrorEnum.GOOGLE_API_ERROR,
            )
